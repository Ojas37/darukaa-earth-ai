import os
import json
import logging
from typing import Dict, Any, List, Optional, Set
import chromadb
from app.rag.ingest import EvidenceIngestor, CORPUS_PATH, CHROMA_DIR

logger = logging.getLogger(__name__)

class EvidenceRetriever:
    """
    Retrieves scientific evidence entries from ChromaDB with metadata pre-filtering,
    per-edge coverage guarantees, and cosine semantic similarity ranking.
    """

    def __init__(self, chroma_dir: Optional[str] = None, collection_name: str = "daruka_evidence"):
        self.ingestor = EvidenceIngestor(chroma_dir=chroma_dir, collection_name=collection_name)
        self.collection = self.ingestor.collection
        
        # In-memory map of full raw corpus entries for rich object return
        self._corpus_cache: Dict[str, Dict[str, Any]] = {}
        self._load_corpus_cache()

        # Ensure collection is populated
        if self.collection.count() == 0:
            logger.info("Chroma collection is empty. Auto-ingesting evidence corpus...")
            self.ingestor.ingest_corpus()

    def _load_corpus_cache(self):
        try:
            entries = self.ingestor.load_corpus()
            self._corpus_cache = {e["id"]: e for e in entries}
        except Exception as e:
            logger.warning(f"Failed to load corpus cache: {e}")

    def retrieve(
        self,
        query: str,
        biome: Optional[str] = None,
        climate_zone: Optional[str] = None,
        edge_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant scientific evidence entries.
        
        When edge_ids is provided:
        - Guarantees at least 1-2 pieces of evidence per active edge_id (if present in corpus).
        - Merges and deduplicates across edges.
        - Ranks by similarity while preserving edge coverage.
        
        When edge_ids is not provided:
        - Filters candidate IDs by biome/climate_zone and ranks top_k by semantic similarity.
        """
        if not self._corpus_cache:
            self._load_corpus_cache()

        # -----------------------------------------------------------------
        # Branch 1: Edge-Guided Retrieval (Guarantees coverage per active edge)
        # -----------------------------------------------------------------
        if edge_ids and len(edge_ids) > 0:
            return self._retrieve_per_edge(
                query=query,
                edge_ids=edge_ids,
                biome=biome,
                climate_zone=climate_zone,
                top_k=top_k
            )

        # -----------------------------------------------------------------
        # Branch 2: Standard Global Filtered Retrieval
        # -----------------------------------------------------------------
        candidate_ids = self._get_matching_candidate_ids(
            biome=biome,
            climate_zone=climate_zone,
            edge_ids=None
        )

        query_params: Dict[str, Any] = {
            "query_texts": [query],
            "n_results": min(top_k, max(len(candidate_ids) if candidate_ids is not None else self.collection.count(), 1))
        }

        if candidate_ids is not None:
            if len(candidate_ids) == 0:
                return []
            query_params["where"] = {"id": {"$in": list(candidate_ids)}}

        results = self.collection.query(**query_params)
        return self._format_chroma_results(results)[:top_k]

    def _retrieve_per_edge(
        self,
        query: str,
        edge_ids: List[str],
        biome: Optional[str],
        climate_zone: Optional[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-1 or top-2 evidence entries for EACH requested edge_id to guarantee
        every active stress pathway has scientific backing, then merges and deduplicates.
        """
        retrieved_map: Dict[str, Dict[str, Any]] = {}

        for edge_id in edge_ids:
            # 1. Find candidate entries that support this edge_id
            edge_candidates = []
            for entry_id, entry in self._corpus_cache.items():
                if edge_id in entry.get("edge_ids", []):
                    # Check biome match (allow "all" or specific match)
                    biome_match = True
                    if biome:
                        entry_biomes = entry.get("biome", [])
                        if "all" not in entry_biomes and biome.lower() not in [b.lower() for b in entry_biomes]:
                            biome_match = False

                    # Check climate_zone match
                    cz_match = True
                    if climate_zone:
                        entry_cz = entry.get("climate_zone", "").lower()
                        if entry_cz not in ["global", "multiple", "all"] and climate_zone.lower() not in entry_cz:
                            cz_match = False

                    if biome_match and cz_match:
                        edge_candidates.append(entry_id)

            # Fallback if strict biome/climate filter yielded no candidates for this edge
            if not edge_candidates:
                edge_candidates = [
                    entry_id for entry_id, entry in self._corpus_cache.items()
                    if edge_id in entry.get("edge_ids", [])
                ]

            if not edge_candidates:
                continue

            # Query Chroma for the top matches for this specific edge
            query_params = {
                "query_texts": [query],
                "n_results": min(2, len(edge_candidates)),
                "where": {"id": {"$in": edge_candidates}}
            }
            results = self.collection.query(**query_params)
            edge_results = self._format_chroma_results(results)

            for entry in edge_results:
                eid = entry["id"]
                if eid not in retrieved_map or entry.get("similarity_score", 0.0) > retrieved_map[eid].get("similarity_score", 0.0):
                    retrieved_map[eid] = entry

        # Collect unique entries across all edges
        all_edge_entries = list(retrieved_map.values())
        
        # Sort by similarity score descending
        all_edge_entries.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)

        # If more entries were retrieved than top_k, ensure we still preserve edge coverage
        # by selecting at least one entry per edge before truncating
        if len(all_edge_entries) > top_k:
            covered_edges = set()
            selected_entries = []
            remaining_entries = []

            for entry in all_edge_entries:
                entry_edges = set(entry.get("edge_ids", []))
                # If this entry covers an edge not yet covered
                if any(e in edge_ids and e not in covered_edges for e in entry_edges):
                    selected_entries.append(entry)
                    covered_edges.update(entry_edges)
                else:
                    remaining_entries.append(entry)

            # Fill up to top_k if room remains
            for entry in remaining_entries:
                if len(selected_entries) < top_k:
                    selected_entries.append(entry)

            return selected_entries

        return all_edge_entries

    def _format_chroma_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Converts Chroma query results into a list of rich dictionary entries."""
        retrieved_entries: List[Dict[str, Any]] = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            doc_ids = results["ids"][0]
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(doc_ids)

            for doc_id, dist in zip(doc_ids, distances):
                similarity = round(max(0.0, min(1.0, 1.0 - (dist / 2.0))), 4)
                raw_entry = self._corpus_cache.get(doc_id)
                if raw_entry:
                    entry_dict = dict(raw_entry)
                else:
                    entry_dict = {"id": doc_id}

                entry_dict["similarity_score"] = similarity
                entry_dict["is_counterpoint"] = bool(
                    "counterpoint" in entry_dict.get("topic", "").lower() or 
                    "guardrail" in entry_dict.get("status", "").lower()
                )
                retrieved_entries.append(entry_dict)

        retrieved_entries.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)
        return retrieved_entries

    def _get_matching_candidate_ids(
        self,
        biome: Optional[str],
        climate_zone: Optional[str],
        edge_ids: Optional[List[str]]
    ) -> Optional[Set[str]]:
        """
        Returns a set of entry IDs that satisfy the specified metadata criteria,
        or None if no filters are applied.
        """
        has_filter = False
        matching_ids: Set[str] = set()

        if not biome and not climate_zone and not edge_ids:
            return None

        for entry_id, entry in self._corpus_cache.items():
            matches_all_criteria = True

            if edge_ids:
                has_filter = True
                entry_edges = entry.get("edge_ids", [])
                if not any(eid in entry_edges for eid in edge_ids):
                    matches_all_criteria = False

            if biome and matches_all_criteria:
                has_filter = True
                entry_biomes = entry.get("biome", [])
                if "all" not in entry_biomes and biome.lower() not in [b.lower() for b in entry_biomes]:
                    matches_all_criteria = False

            if climate_zone and matches_all_criteria:
                has_filter = True
                entry_cz = entry.get("climate_zone", "").lower()
                cz_lower = climate_zone.lower()
                if entry_cz not in ["global", "multiple", "all"] and cz_lower not in entry_cz:
                    matches_all_criteria = False

            if matches_all_criteria:
                matching_ids.add(entry_id)

        return matching_ids if has_filter else None

evidence_retriever = EvidenceRetriever()

import os
import json
import logging
from typing import Dict, Any, List, Optional, Set
import chromadb
from app.rag.ingest import EvidenceIngestor, CORPUS_PATH, CHROMA_DIR

logger = logging.getLogger(__name__)

class EvidenceRetriever:
    """
    Retrieves scientific evidence entries from ChromaDB with metadata pre-filtering
    and cosine semantic similarity ranking.
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
        Filters candidate IDs by metadata (biome, climate_zone, edge_ids) first,
        then ranks candidates by semantic similarity to the query.
        """
        if not self._corpus_cache:
            self._load_corpus_cache()

        # 1. Determine matching candidate IDs based on metadata filters
        candidate_ids = self._get_matching_candidate_ids(
            biome=biome,
            climate_zone=climate_zone,
            edge_ids=edge_ids
        )

        # 2. Query ChromaDB with semantic similarity
        # If candidates are filtered to a non-empty subset, filter by ID list
        query_params: Dict[str, Any] = {
            "query_texts": [query],
            "n_results": min(top_k, max(len(candidate_ids) if candidate_ids else self.collection.count(), 1))
        }

        if candidate_ids is not None:
            if len(candidate_ids) == 0:
                # No candidates matched the strict filter; return empty
                return []
            # ChromaDB supports filtering by ID subset in query
            query_params["where"] = {"id": {"$in": list(candidate_ids)}}

        results = self.collection.query(**query_params)

        retrieved_entries: List[Dict[str, Any]] = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            doc_ids = results["ids"][0]
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(doc_ids)

            for doc_id, dist in zip(doc_ids, distances):
                # Cosine distance to similarity: similarity = 1 - (dist / 2) or 1 - dist
                similarity = round(max(0.0, min(1.0, 1.0 - (dist / 2.0))), 4)
                
                # Fetch full rich entry from cache if available
                raw_entry = self._corpus_cache.get(doc_id)
                if raw_entry:
                    entry_dict = dict(raw_entry)
                else:
                    # Fallback to Chroma metadata
                    entry_dict = {"id": doc_id}

                entry_dict["similarity_score"] = similarity
                entry_dict["is_counterpoint"] = bool(
                    "counterpoint" in entry_dict.get("topic", "").lower() or 
                    "guardrail" in entry_dict.get("status", "").lower()
                )
                retrieved_entries.append(entry_dict)

        # Sort by similarity score descending
        retrieved_entries.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)
        return retrieved_entries[:top_k]

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

        # If no filters specified, return None (search across all)
        if not biome and not climate_zone and not edge_ids:
            return None

        for entry_id, entry in self._corpus_cache.items():
            matches_all_criteria = True

            # Check Edge IDs overlap
            if edge_ids:
                has_filter = True
                entry_edges = entry.get("edge_ids", [])
                if not any(eid in entry_edges for eid in edge_ids):
                    matches_all_criteria = False

            # Check Biome match
            if biome and matches_all_criteria:
                has_filter = True
                entry_biomes = entry.get("biome", [])
                # "all" matches any biome
                if "all" not in entry_biomes and biome.lower() not in [b.lower() for b in entry_biomes]:
                    matches_all_criteria = False

            # Check Climate Zone match
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

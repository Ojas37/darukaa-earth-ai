import os
import json
import logging
from typing import Dict, Any, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

logger = logging.getLogger(__name__)

CORPUS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/knowledge/evidence_corpus.json"))
CHROMA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/knowledge/chroma"))

class EvidenceIngestor:
    """
    Ingests curated scientific evidence entries from evidence_corpus.json into ChromaDB.
    Idempotent: Re-running upserts entries by their unique 'id' without duplicates.
    """

    def __init__(self, chroma_dir: Optional[str] = None, collection_name: str = "daruka_evidence"):
        self.chroma_dir = chroma_dir or CHROMA_DIR
        os.makedirs(self.chroma_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.chroma_dir)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def load_corpus(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        target_path = file_path or CORPUS_PATH
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Evidence corpus file not found at: {target_path}")
        
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("entries", [])

    def ingest_corpus(self, file_path: Optional[str] = None) -> int:
        entries = self.load_corpus(file_path)
        if not entries:
            logger.warning("No entries found in corpus file.")
            return 0

        ids = []
        documents = []
        metadatas = []

        for entry in entries:
            entry_id = entry["id"]
            summary_text = entry["summary"]
            
            # Format metadata for ChromaDB (flat types only)
            metadata = {
                "id": entry_id,
                "topic": entry.get("topic", ""),
                "source": entry.get("source", ""),
                "url": entry.get("url", ""),
                "climate_zone": entry.get("climate_zone", ""),
                "edge_ids": ",".join(entry.get("edge_ids", [])),
                "biome": ",".join(entry.get("biome", [])),
                "status": entry.get("status", ""),
                "caveat": entry.get("caveat") or "",
                "is_counterpoint": bool(
                    "counterpoint" in entry.get("topic", "").lower() or 
                    "guardrail" in entry.get("status", "").lower()
                )
            }

            ids.append(entry_id)
            documents.append(summary_text)
            metadatas.append(metadata)

        # Upsert into Chroma collection (idempotent)
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        logger.info(f"Successfully ingested {len(ids)} evidence entries into collection '{self.collection_name}'.")
        return len(ids)

    def get_count(self) -> int:
        return self.collection.count()

def run_ingest():
    ingestor = EvidenceIngestor()
    count = ingestor.ingest_corpus()
    print(f"[Ingestion Complete] Total documents in collection: {count}")
    return count

if __name__ == "__main__":
    run_ingest()

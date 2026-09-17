# Scientific Knowledge Base & RAG Retrieval Specification — Darukaa.Earth

## 1. Scientific Knowledge Architecture

Darukaa.Earth strictly forbids generating ecological recommendations from unbounded LLM parametric memory. The RAG subsystem connects the multi-metric reasoning engine to a verified, peer-reviewed scientific corpus.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SCIENTIFIC CORPUS SOURCES                          │
│  - FAO Reports (Global Soil Partnership, Agroecology 10 Elements)      │
│  - IPCC Special Reports (Climate Change & Land, 1.5°C)                  │
│  - Peer-Reviewed Journals (Nature Ecology, Soil Biol. & Biochem., etc.) │
│  - SER (Society for Ecological Restoration) Global Standards            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     INGESTION & CLEANING PIPELINE                       │
│  - PDF/Markdown text extraction                                         │
│  - Header & hierarchical section extraction                            │
│  - Metadata tagging (DOI, Authors, Year, Biome, Soil/Climate Tags)      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       SEMANTIC CHUNKING ENGINE                          │
│  - Chunk size: 400 - 800 tokens with 100-token semantic overlap         │
│  - Header hierarchy preserved in chunk preamble                         │
│  - Empirical quantitative statements extracted into metadata summaries   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    EMBEDDING & VECTOR DATABASE                          │
│  - Model: SentenceTransformers (all-MiniLM-L6-v2) / OpenAI text-emb-3   │
│  - Vector Store: ChromaDB / FAISS with IVectorStore abstraction         │
│  - Inverted Metadata Index: Biome, Topic, ClimateZone, InterventionType │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   HYBRID & CONSTRAINED RETRIEVAL                        │
│  - Multi-Query Expansion from Multi-Metric Reasoning Engine             │
│  - Metadata Hard Filtering + Dense Cosine Vector Similarity             │
│  - Reciprocal Rank Fusion & Cross-Encoder Re-ranking                    │
│  - Hard thresholding (Cosine Sim ≥ 0.72)                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Document & Chunk Metadata Schema

Every indexed chunk maintains strict academic provenance:

```json
{
  "chunk_id": "fao_soil_2022_c04_p12_chunk03",
  "document_id": "fao_recarbonization_global_soils_2022",
  "title": "Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices",
  "authors": ["Food and Agriculture Organization of the United Nations (FAO)"],
  "year": 2022,
  "source": "FAO Technical Manual",
  "source_type": "institutional_report",
  "doi_or_url": "https://doi.org/10.4060/cb6386en",
  "topic": "soil_organic_carbon",
  "target_biomes": ["semi_arid", "arid", "sub_humid"],
  "applicable_interventions": ["cover_crops", "residue_retention", "reduced_tillage"],
  "soil_types": ["sandy_loam", "clay_loam", "degraded"],
  "rainfall_range_mm": [250, 700],
  "section_header": "Chapter 4: Cropland Management in Drylands > Residue Management",
  "text": "In semi-arid cropland receiving 300–500 mm annual rainfall, retaining 30% crop residue increased soil organic carbon at a rate of 0.18 ± 0.04 t C/ha/year while improving water infiltration by 22% over a 6-year period...",
  "empirical_metrics": {
    "soc_annual_rate_t_ha": "0.18 +- 0.04",
    "water_infiltration_increase_pct": "22%"
  }
}
```

---

## 3. Scientific Ingestion Pipeline

### 3.1 Text Extraction & Cleaning (`app/rag/ingestion.py`)
1. Ingests scientific PDFs, Markdown files, and JSON datasets from `data/raw/`.
2. Strips noise (running headers, page numbers, licensing boilerplate, bibliographies).
3. Preserves tables and empirical ranges as structured markdown within chunk text.

### 3.2 Semantic Chunking Policy
- Chunks split on natural semantic boundaries (sections, subsections, paragraphs).
- Chunk size: Target **512 tokens** (min: 250, max: 800).
- Overlap: **100 tokens** to prevent boundary fragmentation of causal reasoning chains.
- Every chunk is prepended with its document title, topic, and section hierarchy:
  `[Document: FAO Recarbonizing Soils | Topic: Soil Organic Carbon | Section: Dryland Residues] ...`

### 3.3 Embeddings & Vector Indexing (`app/rag/vector_store.py`)
- Standardized `IEmbeddingProvider` interface allowing seamless switching:
  - Local/Offline: `SentenceTransformer('all-MiniLM-L6-v2')` or `BAAI/bge-small-en-v1.5`
  - Cloud: `OpenAI text-embedding-3-small`
- Standardized `IVectorStore` interface:
  - ChromaDB implementation with persistent SQLite/DuckDB backing.
  - FAISS index implementation for lightweight, zero-dependency in-memory execution.

---

## 4. RAG Retrieval Strategy

### 4.1 Multi-Query Formulation from Environmental Profile
The reasoning engine does not submit the raw user message. It translates the environmental profile and interacting stressors into targeted scientific queries:
- Query 1: *"Soil organic carbon restoration in semi-arid wheat monoculture"*
- Query 2: *"Low rainfall cover crop species selection drought tolerance"*
- Query 3: *"Intercropping soil microbial diversity semi-arid cropland"*

### 4.2 Metadata Pre-Filtering & Dense Vector Search
1. Filter vector index where `target_biomes CONTAINS profile.location.biome` (if specified).
2. Filter where `rainfall_range_mm` encompasses `profile.climate.rainfall_mm_year`.
3. Perform dense vector search across filtered candidate pool.

### 4.3 Reranking & Thresholding
- Similarity scores computed using cosine distance.
- Hard similarity cutoff: Chunks with cosine similarity `< 0.70` are discarded.
- Top $K = 4$ most relevant chunks passed to reasoning and evidence validation.

---

## 5. Anti-Hallucination & Evidence Grounding Guardrails

1. **Explicit Insufficiency Response**: If no retrieved chunks exceed the similarity threshold, the retrieval engine outputs:
   `"Insufficient scientific evidence retrieved for this specific claim."`
   The reasoning engine is prohibited from generating quantitative estimates in this regime.
2. **Preservation of Empirical Uncertainty**: If a study states *"increased by 15–25%"*, the system is forbidden from asserting *"increases by 25%"*. It must cite the published range `15–25%` and attribute it directly to the source.
3. **No Fabricated Citations**: The LLM prompt receives citations only from the `retrieved_chunks` array and is strictly constrained to output citations via `chunk_id` / `doi_or_url` references.

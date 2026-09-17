# Darukaa.Earth — AI Biodiversity Intelligence System

> **A scientifically grounded, multi-metric environmental intelligence platform that models ecological interactions, retrieves peer-reviewed scientific evidence, and generates actionable, non-generic biodiversity restoration recommendations.**

---

## 🌿 Executive Summary

Most generative AI applications treat ecological questions as generic conversational prompts, yielding vague, ungrounded recommendations (e.g., *"practice sustainable farming"* or *"plant trees"*). In reality, biological systems are complex, non-linear networks governed by interdependent physical and biological variables: soil organic carbon, moisture retention, pH dynamics, thermal and precipitation regimes, monoculture pressures, and anthropogenic habitat fragmentation.

**Darukaa.Earth** functions as an **AI Environmental Scientist**. It combines:
1. **Structured Environmental Profiling**: Capturing quantitative and qualitative variables with explicit provenance and uncertainty tracking.
2. **Explicit Environmental Relationship Graphs**: Causal ecological dependency models that govern how soil, land-use, climate, and biodiversity metrics interact.
3. **Dedicated Scientific Knowledge Base & Vector RAG**: Curated peer-reviewed literature, FAO frameworks, and IPCC reports retrieved via hybrid semantic + metadata-filtered vector search.
4. **Multi-Metric Reasoning Engine**: Deterministic stressor identification and candidate intervention evaluation across simultaneous variables.
5. **Scientific Claim Validation & Confidence Scoring**: Anti-hallucination verification ensuring every recommendation, quantitative metric, and timeline is rigorously backed by retrieved citations or conservatively framed.

---

## 🏛️ System Architecture

```
                                  ┌────────────────────────┐
                                  │      User / Client     │
                                  └───────────┬────────────┘
                                              │
                                  ┌───────────▼────────────┐
                                  │ React Scientific UI    │
                                  │ (Dashboard & Chat)     │
                                  └───────────┬────────────┘
                                              │ REST API / WebSocket
                                  ┌───────────▼────────────┐
                                  │   FastAPI Gateway      │
                                  └───────────┬────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       │                                             │
            ┌──────────▼───────────┐                      ┌──────────▼───────────┐
            │ Query Understanding  │                      │ Conversation Memory  │
            │ & Variable Extractor │                      │ & Context Manager    │
            └──────────┬───────────┘                      └──────────┬───────────┘
                       │                                             │
                       └──────────────────────┬──────────────────────┘
                                              │
                                  ┌───────────▼────────────┐
                                  │ Environmental Profile  │
                                  │ (Structured Pydantic)  │
                                  └───────────┬────────────┘
                                              │
                      ┌───────────────────────┼───────────────────────┐
                      │                       │                       │
           ┌──────────▼───────────┐┌──────────▼───────────┐┌──────────▼───────────┐
           │ Missing Information  ││ Environmental Graph  ││ Scientific Vector    │
           │ & Clarification Eng. ││ Causal Relationships ││ RAG Knowledge Base   │
           └──────────────────────┘└──────────┬───────────┘└──────────┬───────────┘
                                              │                       │
                                  ┌───────────▼───────────────────────▼┐
                                  │    Multi-Metric Reasoning Engine   │
                                  │  - Anomaly & Stress Detection      │
                                  │  - Cross-Variable Interaction      │
                                  │  - Candidate Intervention Matrix   │
                                  │  - Constraint Checking             │
                                  └───────────────────┬────────────────┘
                                                      │
                                  ┌───────────────────▼────────────────┐
                                  │       Recommendation Engine        │
                                  │   Actionable Interventions + Why   │
                                  └───────────────────┬────────────────┘
                                                      │
                                  ┌───────────────────▼────────────────┐
                                  │  Scientific Claim Validation &     │
                                  │  Confidence Engine (Anti-Halluc.)  │
                                  └───────────────────┬────────────────┘
                                                      │
                                  ┌───────────────────▼────────────────┐
                                  │   Structured Response Generator    │
                                  └───────────────────┬────────────────┘
                                                      │
                                  ┌───────────────────▼────────────────┐
                                  │  Client Scientific Visualizer      │
                                  └────────────────────────────────────┘
```

---

## 🔬 Core Architectural Pillars

### 1. No LLM-Only Hallucinations
The Large Language Model is isolated to language understanding, synthesis, and explanation. Factual reasoning, stress detection, causal propagation, and metric mapping are driven by the structured environmental profile, the ecological relationship graph, and the verified scientific knowledge base.

### 2. Multi-Metric Co-dependency & Causal Stress Pathways
An intervention is never evaluated in isolation or for a single metric. 
- **Causal Graph Modeling**: An explicit 12-edge ecological graph models multi-hop cascades (e.g. $\text{SOC} \to \text{Infiltration} \to \text{Moisture Deficit} \to \text{Pollinator Food Scarcity} \to \text{Pollinator Decline}$).
- **Maximal Pathway Subsumption**: When multiple sub-chains share the same causal lineage and terminal outcome, the engine automatically selects the maximal root-to-terminal chain. This ensures recommendations tackle root causes (e.g., soil organic carbon building) rather than cosmetic symptoms (e.g., watering downstream). Parallel distinct pathways targeting the same outcome (e.g., pesticide toxicity vs. habitat homogenization $\to$ species richness) are preserved and addressed independently.
- **Ecological Constraint Enforcement**: Strategies are cross-checked against biophysical guardrails (e.g. zero irrigation in semi-arid zones, no-till on fragile low-SOC soils).
- **Study-Weighted Confidence Scoring**: Confidence combines profile data completeness, edge directness, and evidence study design (meta-analyses and institutional IPCC/FAO assessments are weighted above single-site trials).

### 3. Transparent Evidence & Uncertainty
Every recommendation exposes:
- **Mechanisms**: The exact physical/biological chain of causality.
- **Affected Metrics**: Direct and indirect ecological metrics impacted (e.g., Soil Organic Carbon, Microbial Biomass, Pollinator Richness).
- **Time Horizons**: Expected short-term (0-1 yr), medium-term (1-5 yrs), and long-term (5-15 yrs) progressions.
- **Citations**: Specific DOI/source-backed scientific literature.
- **Confidence Rating**: Algorithmic assessment (High / Medium / Low) calculated from input completeness, evidence relevance score, and source consensus.

---

## 📁 Repository Structure

```
darukaa-earth/
├── frontend/                  # React + TypeScript + Vite + Tailwind CSS dashboard
│   ├── src/
│   │   ├── components/        # Profile cards, chat interface, graph visualizer, recommendations
│   │   ├── services/          # API client & streaming hooks
│   │   └── types/             # TypeScript interfaces matching backend schemas
├── backend/                   # Python FastAPI service
│   ├── app/
│   │   ├── api/               # API endpoints (v1 routes)
│   │   ├── core/              # Config, logging, error handling, security
│   │   ├── models/            # Database and vector storage models
│   │   ├── schemas/           # Pydantic schemas (Environmental Profile, Reasoning, Output)
│   │   ├── services/          # LLM Provider abstraction, extraction, ingestion services
│   │   ├── rag/               # Chunking, embeddings, vector indexing, retrieval pipeline
│   │   ├── reasoning/         # Multi-metric engine, stress detection, relationship graph
│   │   ├── recommendations/   # Candidate generation, metric projection, prioritization
│   │   ├── validation/        # Evidence verification & confidence engine
│   │   ├── memory/            # Multi-turn conversation state & context management
│   │   ├── data/              # Structured datasets & relationship graph definitions
│   │   └── main.py            # FastAPI application entrypoint
│   └── tests/                 # Unit, integration, RAG, and reasoning test suites
├── data/
│   ├── raw/                   # Raw scientific documents and open datasets
│   ├── processed/             # Cleaned, structured scientific corpora & JSON benchmarks
│   └── knowledge/             # Pre-built vector indices and relationship graph artifacts
├── docs/                      # Comprehensive technical documentation (Phase 0)
│   ├── architecture.md        # System architecture and data flow
│   ├── data-model.md          # Environmental data model & variable taxonomy
│   ├── rag-design.md          # RAG ingestion, indexing, retrieval, and validation
│   ├── reasoning-engine.md    # Multi-metric reasoning & relationship graph
│   ├── api-design.md          # REST API contracts & JSON schemas
│   └── development-phases.md  # 25-phase roadmap and verification criteria
├── scripts/                   # Ingestion scripts, benchmarking, and database seeds
├── docker/                    # Dockerfiles and orchestration configs
├── .env.example               # Environment variables template
├── docker-compose.yml         # Containerized local execution setup
└── README.md                  # Project overview & quickstart
```

---

## 📊 Environmental Variables Supported

| Category | Primary Metrics | Units / Format |
|---|---|---|
| **Soil** | Soil Organic Carbon (SOC), pH, Moisture Content, Bulk Density | %, pH scale (0-14), %, g/cm³ |
| **Land** | Land Use, Land Cover, Cropping Pattern, Canopy Cover | Categorical / % |
| **Biodiversity** | Species Richness, Habitat Diversity Index, Indicator Taxa | Count, Shannon Index (H'), List |
| **Climate** | Mean Annual Precipitation, Mean Temperature, Aridity Index | mm/year, °C, UNEP AI index |
| **Human Impact** | Chemical Pollution Level, Deforestation Rate, Habitat Fragmentation | Index (Low/Med/High), %/year, Proximity (km) |
| **Geographic** | Latitude, Longitude, Elevation, Agro-Ecological Zone (AEZ) | Dec. Degrees, Meters ASL, FAO AEZ classification |

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic v2, NumPy, Pandas
- **AI & RAG**: Configurable `LLMProvider` (OpenAI / Anthropic / Gemini / Local Ollama), Vector Database (Chroma / FAISS / pgvector), Semantic Chunking, SentenceTransformers / OpenAI Embeddings
- **Knowledge Base**: Curated corpus from FAO, IPCC, Nature Ecology & Evolution, Soil Biology & Biochemistry, Agroforestry Systems
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts
- **Storage**: SQLite (Local Dev) / PostgreSQL (Production), Chroma / FAISS for vector storage
- **Containerization**: Docker & Docker Compose
- **Testing**: Pytest, Pytest-Asyncio, HTTPX

---

## 🚦 Getting Started & Documentation Roadmap

For in-depth specifications, review the dedicated documentation in `/docs`:
- [Architecture & System Flow](docs/architecture.md)
- [Environmental Data Model](docs/data-model.md)
- [Scientific RAG & Knowledge Retrieval](docs/rag-design.md)
- [Multi-Metric Reasoning Engine](docs/reasoning-engine.md)
- [API Design & Contracts](docs/api-design.md)
- [Master Development Phases (0 - 25)](docs/development-phases.md)

---

## ⚖️ License & Scientific Grounding
Built for environmental intelligence research and hackathon demonstration. All recommendations cite scientific literature and adhere to strict evidence-grounding constraints.

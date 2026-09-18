# Darukaa.Earth — AI Biodiversity Intelligence System

> **A scientifically grounded, multi-metric environmental intelligence platform that diagnoses ecological stress cascades, retrieves peer-reviewed scientific literature, and generates actionable, anti-hallucinatory biodiversity restoration recommendations.**

---

## 🌐 Live Deployments

- **Frontend (Vercel Global CDN):** [https://frontend-five-phi-74.vercel.app](https://frontend-five-phi-74.vercel.app)
- **Backend API (FastAPI + ChromaDB):** [https://darukaa-earth-ai.onrender.com](https://darukaa-earth-ai.onrender.com)
- **GitHub Repository:** [https://github.com/Ojas37/darukaa-earth-ai](https://github.com/Ojas37/darukaa-earth-ai)

---

## 🏛️ 1. Architecture Overview

Darukaa employs an **evidence-locked, causal-reasoning architecture** that decouples biological deduction from LLM text generation to prevent hallucinations.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Client Interface (React / Vite)                    │
│    • Real-Time SSE Streamer   • Causal Pathway Graphs   • Metric Diffs  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ REST / Server-Sent Events (SSE)
┌────────────────────────────────────▼────────────────────────────────────┐
│                         FastAPI API Gateway                             │
└───────────────┬─────────────────────────────────────────┬───────────────┘
                │                                         │
┌───────────────▼────────────────────────┐  ┌─────────────▼───────────────┐
│     NLP Variable Extractor & Parser    │  │ Multi-Turn Session Memory   │
│   • Rule & regex clause extractors     │  │ • Profile state transitions │
│   • Active clarification engine        │  │ • Dialogue context & history│
└───────────────┬────────────────────────┘  └─────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────────────────┐
│           Structured Environmental Profile (21 Pydantic Metrics)        │
└───────────────┬─────────────────────────────────────────┬───────────────┘
                │                                         │
┌───────────────▼────────────────────────┐  ┌─────────────▼───────────────┐
│     Ecological Relationship Graph      │  │    ChromaDB Vector Store    │
│  • 18 Causal Stressor Edges (DAG)      │  │  • 19 Peer-Reviewed Studies │
│  • Fixed-point multi-hop propagation   │  │  • Cosine Semantic Search   │
│  • Maximal pathway subsumption         │  │  • Per-Edge Evidence Floor  │
└───────────────┬────────────────────────┘  └─────────────┬───────────────┘
                │                                         │
┌───────────────▼─────────────────────────────────────────▼───────────────┐
│                    Multi-Metric Recommendation Engine                   │
│   • Biophysical Guardrails (e.g. zero irrigation in semi-arid zones)    │
│   • LLM Synthesis (Claude 3.5 Sonnet / Groq LLaMA-3.3 70B)              │
│   • Automated Claim Validator (verifies all metrics against citations)  │
│   • Deterministic Confidence Scorer (0.0 – 1.0)                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ 2. Database & Data Schema

### A. Environmental Profile (`Pydantic v2`)
Tracks **21 standardized ecological variables** across 5 physical and biological domains:

```python
class EnvironmentalProfile(BaseModel):
    location: LocationProfile        # Biome, Region, Coordinates, Elevation
    soil: SoilProfile                # pH, SOC (%), Moisture (%), Bulk Density, Texture
    land: LandProfile                # Land Use, Land Cover, Cropping Pattern, Tillage, Canopy (%)
    biodiversity: BiodiversityProfile# Species Richness, Pollinators, Soil Biology, Issues List
    climate: ClimateProfile          # Rainfall (mm/yr), Pattern, Mean Temp (°C), Aridity Index
    human_impact: HumanImpactProfile # Pollution Level & Types, Deforestation, Fragmentation
```

- **Provenance & Uncertainty**: Every field tracks its `ValueStatus` (`provided`, `estimated`, `unknown`, `missing`), numeric confidence score ($0.0 - 1.0$), and raw text citation.
- **Completeness Formula**: $\text{Completeness} = \frac{\text{Known Metrics}}{21 \text{ Total Metrics}}$.

### B. Vector Knowledge Base (`ChromaDB`)
- **Storage**: Persistent embedded ChromaDB instance (`data/knowledge/chroma/`).
- **Corpus**: 19 curated, traceable studies from **IPCC, FAO, Nature Communications, Journal of Environmental Quality, and Ecological Engineering**.
- **Indexing**: Cosine space with mandatory similarity floors ($\ge 0.50$) to reject ungrounded or forced citations.

---

## 💻 3. Local Development Setup

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & `npm`
- **Groq API Key** *(free tier)* or **Anthropic API Key**

### 1. Clone the Repository
```bash
git clone https://github.com/Ojas37/darukaa-earth-ai.git
cd darukaa-earth-ai
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
# Optional:
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Start the FastAPI development server:
```bash
uvicorn app.main:app --reload --port 8000
```
*API Docs available at: `http://localhost:8000/docs`*

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```
*Frontend running at: `http://localhost:5173`*

---

## 🚀 4. CI/CD & Cloud Deployment

The repository is configured for automated, zero-downtime continuous deployment:

### A. Frontend Deployment (Vercel)
- **Framework Preset**: `Vite`
- **Root Directory**: `frontend`
- **Build Command**: `npm run build` (`tsc -b && vite build`)
- **Output Directory**: `dist`
- **Environment Variable**: `VITE_API_BASE_URL=https://darukaa-earth-ai.onrender.com`
- **Deployment Trigger**: Auto-deployed on every push to `main` via Vercel GitHub integration.

### B. Backend Deployment (Render Blueprint)
Configured via [`render.yaml`](render.yaml) Infrastructure-as-Code:
```yaml
services:
  - type: web
    name: darukaa-backend
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    plan: free
    autoDeploy: true
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.12
      - key: GROQ_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
```

---

## 🧪 5. Verification & Testing

Run the full automated test suite:
```bash
# Backend unit, reasoning, and RAG tests:
cd backend
pytest tests/ -v

# Frontend TypeScript and bundle build check:
cd ../frontend
npm run build
```

---

## ⚖️ License
Built for ecological intelligence research and hackathon demonstration. All recommendations cite peer-reviewed literature and enforce strict anti-hallucinatory guardrails.

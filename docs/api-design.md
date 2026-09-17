# REST API Design & Contracts — Darukaa.Earth

## 1. API Architecture Overview

The Darukaa.Earth backend exposes a high-performance REST API built on FastAPI. All request and response bodies adhere strictly to typed Pydantic v2 schemas.

- **Base URL**: `/api/v1`
- **Protocol**: HTTP/1.1 and HTTP/2 over TLS (WebSocket support for real-time multi-agent streaming)
- **Content-Type**: `application/json`

---

## 2. API Endpoints Specification

### 2.1 System Health
#### `GET /health`
Returns the operational health of the application, vector database connectivity, and configured LLM provider status.

**Response `200 OK`:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-09-17T23:25:00Z",
  "components": {
    "api_gateway": "healthy",
    "vector_store": "healthy",
    "relationship_graph": "loaded (28 nodes, 46 edges)",
    "llm_provider": "gemini-3.7-flash (connected)"
  }
}
```

---

### 2.2 Conversational Interaction & Extraction
#### `POST /api/v1/chat`
The primary conversational endpoint. Receives user natural language input, updates session memory, extracts structured variables, checks for missing data, and triggers multi-metric reasoning when ready.

**Request Body:**
```json
{
  "conversation_id": "conv_9b83a21e",
  "message": "My crop yield and wild pollinators have plummeted. I'm farming 50 hectares of monoculture wheat in a semi-arid plateau with very low rainfall. Soil tests show organic carbon is only 0.35%."
}
```

**Response `200 OK` (Full Analysis Mode):**
```json
{
  "conversation_id": "conv_9b83a21e",
  "turn_id": "turn_001",
  "needs_clarification": false,
  "missing_information": [],
  "extracted_variables": {
    "location": {"region_name": "semi-arid plateau", "biome": "semi_arid"},
    "soil": {"organic_carbon_percent": {"value": 0.35, "unit": "%", "status": "provided"}},
    "land": {"cropping_pattern": {"value": "monoculture", "status": "provided"}, "land_use": {"value": "cropland", "status": "provided"}},
    "climate": {"rainfall_mm_year": {"value": 350.0, "unit": "mm/year", "status": "estimated"}},
    "biodiversity": {"pollinator_presence": {"value": "scarce", "status": "provided"}}
  },
  "assessment": {
    "detected_stressors": [
      {
        "variable": "soil.organic_carbon_percent",
        "severity": "critical",
        "condition": "Severe carbon depletion (<0.4%)",
        "ecological_risk": "Impaired microbial nutrient cycling & diminished soil moisture retention"
      },
      {
        "variable": "land.cropping_pattern",
        "severity": "high",
        "condition": "Monoculture cropping",
        "ecological_risk": "Floral & structural homogenization causing pollinator habitat collapse"
      }
    ],
    "interacting_mechanisms": [
      "Low SOC (0.35%) + Low Rainfall (<400mm) creates severe water retention deficits and rhizosphere stress.",
      "Monoculture wheat eliminates nectar/pollen floral corridors, causing observed pollinator crash."
    ]
  },
  "recommendations": [
    {
      "id": "rec_01",
      "action": "Introduce drought-tolerant legume intercropping (e.g., Cajanus cajan / Vigna aconitifolia) and permanent native floral insectary strips.",
      "why_it_works": "Legume intercropping fixes atmospheric nitrogen and contributes labile organic residues to build SOC without competing for peak irrigation, while flowering perimeter strips restore continuous foraging habitat for wild pollinators.",
      "affected_metrics": [
        {"metric": "Soil Organic Carbon", "expected_direction": "+0.15–0.25 t C/ha/yr", "time_horizon": "medium_term (2-4 yrs)"},
        {"metric": "Pollinator Abundance", "expected_direction": "+40–60% floral visits", "time_horizon": "short_term (1 yr)"},
        {"metric": "Soil Moisture Retention", "expected_direction": "+15–20% infiltration", "time_horizon": "medium_term (3 yrs)"}
      ],
      "time_horizon": {
        "short_term": "Establish flowering field margins and insectary strips within months 1–3.",
        "medium_term": "Transition from wheat monoculture to strip-intercropping across seasons 1–3.",
        "long_term": "Accumulate stable humus fractions and rebuild fungal-to-bacterial soil biomass."
      },
      "confidence": "High (0.86)",
      "confidence_breakdown": {
        "profile_completeness": 0.85,
        "evidence_similarity": 0.88,
        "graph_support": 0.90,
        "source_consensus": 0.82
      },
      "evidence": [
        {
          "chunk_id": "fao_soil_2022_c04_chunk03",
          "title": "Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices",
          "source": "FAO Technical Manual (2022)",
          "doi_or_url": "https://doi.org/10.4060/cb6386en",
          "relevance_score": 0.91,
          "excerpt": "In semi-arid drylands, drought-adapted legume intercrops increased SOC by 0.18 t C/ha/yr while boosting pollinator species richness."
        }
      ],
      "uncertainties": [
        "Exact baseline soil pH is unknown; legume Rhizobium nodulation efficiency may vary if soil pH is <5.5."
      ]
    }
  ],
  "clarification_prompt": null
}
```

**Response `200 OK` (Clarification Mode):**
When the user query contains insufficient information (e.g. *"My biodiversity is declining"*):
```json
{
  "conversation_id": "conv_9b83a21e",
  "turn_id": "turn_001",
  "needs_clarification": true,
  "missing_information": [
    {
      "field": "soil.organic_carbon_percent",
      "prompt": "What is your approximate soil organic carbon or soil quality (e.g., sandy, degraded, dark loam)?",
      "priority": 1
    },
    {
      "field": "climate.rainfall_mm_year",
      "prompt": "What is the typical rainfall pattern or geographic region (e.g., semi-arid, high rainfall, Mediterranean)?",
      "priority": 2
    },
    {
      "field": "land.cropping_pattern",
      "prompt": "Is the land under single-crop monoculture, pasture, or mixed cropping?",
      "priority": 3
    }
  ],
  "extracted_variables": {
    "biodiversity": {"species_richness": {"status": "provided", "source_notes": "declining"}}
  },
  "assessment": null,
  "recommendations": [],
  "clarification_prompt": "I can help analyze the drivers of biodiversity decline on your land. To provide scientifically grounded recommendations, could you share:\n1. Your soil type or organic carbon level\n2. The rainfall pattern or geographic region\n3. The current land use or cropping practice\n\nIf you don't know exact numbers, qualitative descriptions work well too!"
}
```

---

### 2.3 Environmental Profile Endpoints
#### `POST /api/v1/environment/extract`
Extracts structured environmental variables from raw text without triggering recommendation reasoning.

#### `GET /api/v1/environment/{conversation_id}`
Retrieves the accumulated, normalized `EnvironmentalProfile` for an active session.

#### `PUT /api/v1/environment/{conversation_id}`
Directly updates or overrides specific environmental fields in the active session.

---

### 2.4 Multi-Metric Reasoning & Knowledge Endpoints
#### `POST /api/v1/reasoning/analyze`
Executes the multi-metric reasoning pipeline on a provided `EnvironmentalProfile` payload.

#### `POST /api/v1/knowledge/search`
Direct vector similarity search across the scientific knowledge base.

**Request Body:**
```json
{
  "query": "soil organic carbon restoration cover crops drylands",
  "filter_biome": "semi_arid",
  "top_k": 3
}
```

---

### 2.5 Demo Scenarios Endpoint
#### `GET /api/v1/demo/scenarios`
Returns pre-packaged benchmark scenarios (Semi-Arid Monoculture, Habitat Fragmentation, Agrochemical Runoff, Incomplete Inquiry) for evaluation and hackathon judging.

---

## 3. Standard Error Envelope

All API errors return a standard HTTP error payload:

```json
{
  "error": {
    "code": "INVALID_ENVIRONMENTAL_VALUE",
    "message": "Validation failed: soil.ph value 16.5 exceeds physical bound [0.0 - 14.0]",
    "field": "soil.ph",
    "timestamp": "2026-09-17T23:25:00Z"
  }
}
```

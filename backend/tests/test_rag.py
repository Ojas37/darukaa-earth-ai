import pytest
from app.rag.ingest import EvidenceIngestor
from app.rag.retrieval import EvidenceRetriever
from app.rag.validation import ClaimValidator
from app.schemas.profile import EnvironmentalProfile, ValueStatus, EnvironmentalMetric
from app.reasoning.relationship_graph import relationship_graph

@pytest.fixture(scope="module")
def ingestor():
    ing = EvidenceIngestor(collection_name="test_daruka_evidence")
    ing.ingest_corpus()
    return ing

@pytest.fixture(scope="module")
def retriever(ingestor):
    return EvidenceRetriever(collection_name="test_daruka_evidence")

@pytest.fixture
def validator():
    return ClaimValidator()

def test_ingestion_count_and_idempotency(ingestor):
    # Ingest should load exactly 16 entries
    count1 = ingestor.get_count()
    assert count1 == 16

    # Re-running ingestion should not duplicate entries (idempotent upsert)
    count2 = ingestor.ingest_corpus()
    assert count2 == 16
    assert ingestor.get_count() == 16

def test_retrieval_with_biome_and_climate_filter(retriever):
    # Query with semi_arid biome filter
    results_semi_arid = retriever.retrieve(
        query="water infiltration and soil degradation",
        biome="semi_arid",
        top_k=5
    )
    assert len(results_semi_arid) > 0
    for r in results_semi_arid:
        biomes = r.get("biome", [])
        assert "all" in biomes or "semi_arid" in biomes

    # Query with tropical biome filter
    results_tropical = retriever.retrieve(
        query="microclimate canopy cover temperature buffering",
        biome="tropical",
        top_k=5
    )
    assert len(results_tropical) > 0
    for r in results_tropical:
        biomes = r.get("biome", [])
        assert "all" in biomes or "tropical" in biomes or "forest" in biomes

def test_validation_flags_fabricated_number(validator, retriever):
    retrieved = retriever.retrieve(query="soil water infiltration cover crops", top_k=3)
    
    # Fabricated number (92.7% is not in the corpus)
    fabricated_claim = "Introducing specialized cover crops raises soil water infiltration rates by 92.7%."
    result = validator.validate_claim(fabricated_claim, retrieved)

    assert result.is_valid is False
    assert any("92.7" in num for num in result.unsupported_numbers)
    assert result.rewritten_claim is not None
    assert "92.7" not in result.rewritten_claim
    assert "substantially" in result.rewritten_claim or "measurable" in result.rewritten_claim

def test_validation_passes_grounded_number(validator, retriever):
    retrieved = retriever.retrieve(query="Basche DeLonge cover crops infiltration", top_k=3)
    
    # Grounded numbers from ev_001 (59% and 35%)
    grounded_claim = "A meta-analysis found introducing perennials raised infiltration by 59%, and cover crops by 35%."
    result = validator.validate_claim(grounded_claim, retrieved)

    assert result.is_valid is True
    assert len(result.unsupported_numbers) == 0
    assert "59%" in result.supported_numbers or "59" in result.supported_numbers
    assert "35%" in result.supported_numbers or "35" in result.supported_numbers

def test_validation_surfaces_counterpoints(validator, retriever):
    # Retrieve evidence including ev_002 counterpoint
    retrieved = retriever.retrieve(query="Rawls plant-available water capacity counterpoint", top_k=5)
    
    claim = "Soil organic carbon increases water infiltration."
    result = validator.validate_claim(claim, retrieved)

    assert len(result.active_counterpoints) > 0
    assert any("ev_002" == cp.get("id") for cp in result.active_counterpoints)

def test_case_b_edge_filtered_retrieval(retriever):
    """
    Case B: semi-arid, 0.35% SOC, monoculture wheat, 350mm rainfall.
    Active edges include:
    - edge_soc_to_infiltration
    - edge_infiltration_to_moisture_stress
    - edge_monoculture_to_homogenization
    """
    profile_b = EnvironmentalProfile()
    profile_b.location.biome = "semi_arid"
    profile_b.soil.organic_carbon_percent = EnvironmentalMetric[float](value=0.35, status=ValueStatus.PROVIDED)
    profile_b.land.cropping_pattern = EnvironmentalMetric[str](value="monoculture", status=ValueStatus.PROVIDED)
    profile_b.climate.rainfall_mm_year = EnvironmentalMetric[float](value=350.0, status=ValueStatus.PROVIDED)

    # Discover active pathways and edge IDs
    pathways = relationship_graph.find_stress_pathways(profile_b, min_length=2)
    active_edge_ids = list(set([edge.id for p in pathways for edge in p.edges]))

    # Retrieve evidence filtered by active edges and biome
    results = retriever.retrieve(
        query="dryland cropland restoration soil carbon and crop diversity",
        biome="semi_arid",
        edge_ids=active_edge_ids,
        top_k=5
    )

    assert len(results) > 0
    retrieved_ids = [r["id"] for r in results]
    # Check that high-relevance evidence for dryland infiltration/degradation or homogenization is returned
    assert any(eid in ["ev_001", "ev_002", "ev_008", "ev_014", "ev_015"] for eid in retrieved_ids)

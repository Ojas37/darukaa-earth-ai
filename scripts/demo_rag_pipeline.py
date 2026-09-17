import json
from app.rag.ingest import EvidenceIngestor
from app.rag.retrieval import evidence_retriever
from app.rag.validation import claim_validator
from app.schemas.profile import EnvironmentalProfile, ValueStatus, EnvironmentalMetric
from app.reasoning.relationship_graph import relationship_graph

def run_rag_demonstration():
    print("================================================================================")
    print("DARUKAA.EARTH - SCIENTIFIC KNOWLEDGE RETRIEVAL & VALIDATION DEMO")
    print("================================================================================\n")

    # 1. Ingestion Status
    ingestor = EvidenceIngestor()
    total_docs = ingestor.ingest_corpus()
    print(f"[1] Ingestion Status: {total_docs} verified scientific entries indexed in ChromaDB.\n")

    # 2. Query 1: Semi-Arid Soil & Infiltration
    print("-" * 80)
    print("SAMPLE QUERY 1: 'soil water infiltration and cover crops' (Filtered: Biome=semi_arid)")
    print("-" * 80)
    results_1 = evidence_retriever.retrieve(
        query="soil water infiltration and cover crops",
        biome="semi_arid",
        top_k=3
    )
    for r in results_1:
        print(f"[{r['id']}] Score: {r.get('similarity_score')} | Biome: {r.get('biome')} | Counterpoint: {r.get('is_counterpoint')}")
        print(f"  Topic: {r['topic']}")
        print(f"  Summary: {r['summary']}")
        print(f"  Source: {r['source']} ({r['url']})")
        if r.get('caveat'):
            print(f"  Caveat: {r['caveat']}")
        print()

    # 3. Query 2: Tropical Forest & Canopy Cover Microclimate Buffering
    print("-" * 80)
    print("SAMPLE QUERY 2: 'canopy cover deforestation microclimate warming' (Filtered: Biome=forest)")
    print("-" * 80)
    results_2 = evidence_retriever.retrieve(
        query="canopy cover deforestation microclimate warming",
        biome="forest",
        top_k=2
    )
    for r in results_2:
        print(f"[{r['id']}] Score: {r.get('similarity_score')} | Biome: {r.get('biome')}")
        print(f"  Topic: {r['topic']}")
        print(f"  Summary: {r['summary']}")
        print(f"  Source: {r['source']} ({r['url']})")
        print()

    # 4. Query 3: Multi-Edge Filtered Retrieval for Case B Profile
    print("-" * 80)
    print("SAMPLE QUERY 3: Edge-Filtered Retrieval for Case B (Semi-Arid 0.35% SOC Wheat Monoculture)")
    print("-" * 80)
    profile_b = EnvironmentalProfile()
    profile_b.location.biome = "semi_arid"
    profile_b.soil.organic_carbon_percent = EnvironmentalMetric[float](value=0.35, status=ValueStatus.PROVIDED)
    profile_b.land.cropping_pattern = EnvironmentalMetric[str](value="monoculture", status=ValueStatus.PROVIDED)
    profile_b.climate.rainfall_mm_year = EnvironmentalMetric[float](value=350.0, status=ValueStatus.PROVIDED)

    pathways = relationship_graph.find_stress_pathways(profile_b, min_length=2)
    active_edge_ids = list(set([e.id for p in pathways for e in p.edges]))
    print(f"Active Edge IDs passed to RAG: {active_edge_ids}\n")

    results_3 = evidence_retriever.retrieve(
        query="dryland restoration crop diversification and soil moisture",
        biome="semi_arid",
        edge_ids=active_edge_ids,
        top_k=3
    )
    for r in results_3:
        print(f"[{r['id']}] Linked Edges: {r.get('edge_ids')} | Score: {r.get('similarity_score')}")
        print(f"  Summary: {r['summary']}")
        print(f"  Source: {r['source']}\n")

    # 5. Anti-Hallucination Claim Validation Demonstration
    print("=" * 80)
    print("ANTI-HALLUCINATION & EVIDENCE GROUNDING DEMONSTRATION")
    print("=" * 80)

    # Test Grounded Claim
    grounded_claim = "Introducing perennials raised infiltration rates by about 59%, and cover crops by 35% relative to conventional management."
    val_grounded = claim_validator.validate_claim(grounded_claim, results_1)
    print("\nClaim A (Grounded with real numbers from ev_001):")
    print(f"  \"{grounded_claim}\"")
    print(f"  Valid: {val_grounded.is_valid} | Supported Numbers: {val_grounded.supported_numbers}")

    # Test Fabricated Claim
    hallucinated_claim = "Cover crops increase soil organic carbon by 48.5% and boost water retention by 92% in 6 months."
    val_hallucinated = claim_validator.validate_claim(hallucinated_claim, results_1)
    print("\nClaim B (Hallucinated numbers 48.5% and 92%):")
    print(f"  \"{hallucinated_claim}\"")
    print(f"  Valid: {val_hallucinated.is_valid}")
    print(f"  Flagged Unsupported Numbers: {val_hallucinated.unsupported_numbers}")
    print(f"  Rewritten Qualitative Guidance: \"{val_hallucinated.rewritten_claim}\"")

if __name__ == "__main__":
    run_rag_demonstration()

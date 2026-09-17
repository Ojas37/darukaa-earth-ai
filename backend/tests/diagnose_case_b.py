"""
Diagnostic Script for Case B Recommendations and Confidence Breakdown
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.profile import (
    EnvironmentalProfile, EnvironmentalMetric, ValueStatus
)
from app.reasoning.relationship_graph import relationship_graph
from app.recommendations.generator import (
    RecommendationGenerator, _compute_confidence, _build_constraint_instructions
)
from app.rag.retrieval import evidence_retriever

profile = EnvironmentalProfile()
profile.location.biome = "semi_arid"
profile.location.region_name = "Semi-Arid Wheat Belt"
profile.soil.organic_carbon_percent = EnvironmentalMetric[float](
    value=0.35, unit="%", status=ValueStatus.PROVIDED, confidence=1.0, raw_input="SOC 0.35%"
)
profile.soil.ph = EnvironmentalMetric[float](
    value=7.2, unit="pH", status=ValueStatus.PROVIDED, confidence=1.0
)
profile.land.cropping_pattern = EnvironmentalMetric[str](
    value="monoculture", status=ValueStatus.PROVIDED, confidence=1.0
)
profile.land.primary_crops = ["wheat"]
profile.land.land_use = EnvironmentalMetric[str](value="cropland", status=ValueStatus.PROVIDED)
profile.climate.rainfall_mm_year = EnvironmentalMetric[float](
    value=350.0, unit="mm/year", status=ValueStatus.PROVIDED, confidence=1.0
)
profile.climate.rainfall_pattern = EnvironmentalMetric[str](
    value="low_rainfall_semi_arid", status=ValueStatus.PROVIDED
)
profile.biodiversity.pollinator_presence = EnvironmentalMetric[str](
    value="scarce", status=ValueStatus.PROVIDED
)
profile.biodiversity.observed_issues = ["pollinator_decline"]

pathways = relationship_graph.find_stress_pathways(profile, min_length=2)
print(f"Total pathways discovered: {len(pathways)}")

generator = RecommendationGenerator()

# Generate recommendations without the start/terminal dedup so we can inspect all pathways
raw_recs = []
constraint_instructions, constraint_notes_list = _build_constraint_instructions(profile)

for i, p in enumerate(pathways, 1):
    print(f"\n{'='*80}")
    print(f"PATHWAY {i}: [{p.pathway_id}] {' → '.join(p.nodes)}")
    print(f"Summary: {p.summary}")
    print(f"Confidence (graph): {p.confidence.value}")
    
    # Check retrieved evidence
    active_edge_ids = [e.id for e in p.edges]
    query = (
        f"biodiversity restoration intervention "
        f"{profile.location.biome or 'cropland'} "
        f"{' '.join(e.source_node.split('.')[-1] for e in p.edges)}"
    )
    retrieved_evidence = evidence_retriever.retrieve(
        query=query,
        biome=profile.location.biome,
        climate_zone="low_rainfall_semi_arid",
        edge_ids=active_edge_ids,
        top_k=3,
    )
    
    print(f"\n--- Retrieved Evidence ({len(retrieved_evidence)} items) ---")
    for ev in retrieved_evidence:
        print(f"  [{ev.get('id')}] sim={ev.get('similarity_score', 0):.3f} | is_counterpoint={ev.get('is_counterpoint', False)} | source={ev.get('source')}")
        print(f"      edge_ids={ev.get('edge_ids')}")
        print(f"      summary={ev.get('summary')[:100]}...")

    # Score breakdown
    score, basis = _compute_confidence(p, profile, retrieved_evidence)
    print(f"\n--- Confidence Computation ---")
    print(f"  Score: {score}")
    print(f"  Basis: {basis}")

    rec = generator._generate_for_pathway(
        profile=profile,
        pathway=p,
        constraint_instructions=constraint_instructions,
        constraint_notes_list=constraint_notes_list,
        top_k_evidence_per_edge=3
    )
    raw_recs.append((p, rec))
    if rec:
        print(f"\n--- Generated Recommendation ---")
        print(f"  Recommendation:\n  {rec.recommendation}")
        print(f"\n  Why It Works:\n  {rec.why_it_works}")
        print(f"\n  Affected Metrics: {rec.affected_metrics}")
        print(f"  Time Horizon: {rec.time_horizon}")
        print(f"  Evidence Citations: {len(rec.evidence)}")
        for cit in rec.evidence:
            print(f"    - {cit.source}: {cit.claim_supported}")
        print(f"  Warnings: {rec.validation_warnings}")

print(f"\n{'='*80}")
print("SIDE-BY-SIDE COMPARISON OF ALL RECOMMENDATIONS")
print(f"{'='*80}")
for idx, (p, r) in enumerate(raw_recs, 1):
    print(f"\nREC {idx} (Pathway {p.pathway_id}):")
    print(f"  Chain: {' → '.join(p.nodes)}")
    if r:
        print(f"  Recommendation: {r.recommendation}")
        print(f"  Why It Works:   {r.why_it_works}")
        print(f"  Confidence:     {r.confidence_score} ({r.confidence_basis})")
    else:
        print("  FAILED TO GENERATE")

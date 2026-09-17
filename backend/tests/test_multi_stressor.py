"""
Sanity check: Multi-Stressor Synthetic Profile (Case C)
Triggers 4 distinct root causes:
1. Low SOC & Low Rainfall (Soil/Hydrology/Pollinator)
2. Monoculture (Landscape structural homogenization)
3. Deforestation (Microclimate buffering loss / heat stress)
4. Agrochemical Pollution (Ecotoxicity / biodiversity loss)
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.profile import (
    EnvironmentalProfile, EnvironmentalMetric, ValueStatus
)
from app.reasoning.relationship_graph import relationship_graph
from app.recommendations.generator import RecommendationGenerator

profile = EnvironmentalProfile()
profile.location.biome = "tropical_dry_forest"
profile.location.region_name = "Sub-Tropical Agricultural Margin"

profile.soil.organic_carbon_percent = EnvironmentalMetric[float](
    value=0.45, unit="%", status=ValueStatus.PROVIDED, confidence=1.0, raw_input="SOC 0.45%"
)
profile.soil.ph = EnvironmentalMetric[float](
    value=6.8, unit="pH", status=ValueStatus.PROVIDED, confidence=1.0
)
profile.land.cropping_pattern = EnvironmentalMetric[str](
    value="monoculture", status=ValueStatus.PROVIDED, confidence=1.0
)
profile.land.primary_crops = ["cotton"]
profile.land.land_use = EnvironmentalMetric[str](value="cropland", status=ValueStatus.PROVIDED)

profile.climate.rainfall_mm_year = EnvironmentalMetric[float](
    value=420.0, unit="mm/year", status=ValueStatus.PROVIDED, confidence=1.0
)
profile.climate.rainfall_pattern = EnvironmentalMetric[str](
    value="low_rainfall_semi_arid", status=ValueStatus.PROVIDED
)
profile.climate.temperature_mean_c = EnvironmentalMetric[float](
    value=33.5, unit="°C", status=ValueStatus.PROVIDED, confidence=1.0
)

profile.human_impact.deforestation_history = EnvironmentalMetric[str](
    value="recent", status=ValueStatus.PROVIDED, confidence=1.0
)
profile.human_impact.pollution_level = EnvironmentalMetric[str](
    value="high", status=ValueStatus.PROVIDED, confidence=1.0
)
profile.human_impact.pollution_types = ["pesticides", "synthetic_fertilizer"]

profile.biodiversity.pollinator_presence = EnvironmentalMetric[str](
    value="scarce", status=ValueStatus.PROVIDED
)
profile.biodiversity.observed_issues = ["pollinator_decline", "biodiversity_loss"]

print("\n" + "═" * 75)
print("DARUKAA.EARTH — Sanity Check: Multi-Stressor Profile (Case C)")
print("═" * 75)

pathways = relationship_graph.find_stress_pathways(profile, min_length=2)
print(f"\n✓ Active stress pathways discovered: {len(pathways)}")
for p in pathways:
    print(f"  [{p.pathway_id}] {' → '.join(p.nodes)} (conf={p.confidence.value})")

generator = RecommendationGenerator()
print(f"\n→ Generating recommendations across active pathways...")
recs = generator.generate(profile=profile, pathways=pathways)

print(f"\n✓ Total Distinct Recommendations Generated: {len(recs)}")
for idx, r in enumerate(recs, 1):
    print(f"\n[{idx}] Pathway ID: {r.pathway_id}")
    print(f"    Recommendation  : {r.recommendation}")
    print(f"    Why It Works    : {r.why_it_works}")
    print(f"    Affected Metrics: {r.affected_metrics}")
    print(f"    Time Horizon    : {r.time_horizon}")
    print(f"    Confidence Score: {r.confidence_score:.3f} ({r.confidence_basis})")
    print(f"    Citations ({len(r.evidence)}):")
    for cit in r.evidence:
        print(f"      • {cit.source}: {cit.claim_supported}")
    if r.constraint_notes:
        print(f"    Constraint Notes: {r.constraint_notes}")

assert len(recs) >= 3, f"Expected at least 3 distinct recommendations, got {len(recs)}"
print("\n" + "═" * 75)
print("SANITY CHECK PASSED: 3+ distinct recommendations successfully generated ✓")
print("═" * 75)

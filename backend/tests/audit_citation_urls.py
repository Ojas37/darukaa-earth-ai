"""
Audit Citation URL Provenance across Case B and Case C
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.profile import EnvironmentalProfile, EnvironmentalMetric, ValueStatus
from app.reasoning.relationship_graph import relationship_graph
from app.recommendations.generator import RecommendationGenerator

# Load ground truth evidence corpus
corpus_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data", "knowledge", "evidence_corpus.json")
with open(corpus_path, "r", encoding="utf-8") as f:
    corpus_data = json.load(f)

corpus_by_id = {e["id"]: e for e in corpus_data["entries"]}
corpus_by_source_fragment = {}
for e in corpus_data["entries"]:
    # index by first few author words
    first_author = e["source"].split(",")[0].split()[0].lower()
    corpus_by_source_fragment[first_author] = e

print("Loaded corpus entries:", len(corpus_by_id))

generator = RecommendationGenerator()

def audit_profile(name: str, profile: EnvironmentalProfile):
    print("\n" + "═" * 80)
    print(f"AUDITING: {name}")
    print("═" * 80)
    pathways = relationship_graph.find_stress_pathways(profile, min_length=2)
    recs = generator.generate(profile=profile, pathways=pathways)
    
    for idx, r in enumerate(recs, 1):
        print(f"\n--- Recommendation {idx} (Pathway: {r.pathway_id}) ---")
        print(f"Text: {r.recommendation[:100]}...")
        print(f"Citations count: {len(r.evidence)}")
        for c in r.evidence:
            output_url = c.url
            # Match to corpus
            matched_entry = None
            for eid, entry in corpus_by_id.items():
                if entry["source"] == c.source or entry["url"] == c.url:
                    matched_entry = entry
                    break
                # Check partial match on author
                c_author = c.source.split(",")[0].split()[0].lower() if c.source else ""
                e_author = entry["source"].split(",")[0].split()[0].lower()
                if c_author and c_author in e_author:
                    matched_entry = entry
                    break
            
            corpus_url = matched_entry["url"] if matched_entry else "NOT_FOUND_IN_CORPUS"
            corpus_id = matched_entry["id"] if matched_entry else "UNKNOWN"
            is_match = (output_url == corpus_url)
            
            print(f"\n  Citation: {c.source[:60]}...")
            print(f"    • Matched Corpus ID : {corpus_id}")
            print(f"    • Final Output URL  : {output_url}")
            print(f"    • Corpus JSON URL   : {corpus_url}")
            print(f"    • Byte-Identical?   : {'✓ YES' if is_match else '✗ NO (MISMATCH)'}")

# Build Case B
p_b = EnvironmentalProfile()
p_b.location.biome = "semi_arid"
p_b.location.region_name = "Semi-Arid Wheat Belt"
p_b.soil.organic_carbon_percent = EnvironmentalMetric[float](value=0.35, unit="%", status=ValueStatus.PROVIDED, confidence=1.0)
p_b.soil.ph = EnvironmentalMetric[float](value=7.2, unit="pH", status=ValueStatus.PROVIDED, confidence=1.0)
p_b.land.cropping_pattern = EnvironmentalMetric[str](value="monoculture", status=ValueStatus.PROVIDED, confidence=1.0)
p_b.climate.rainfall_mm_year = EnvironmentalMetric[float](value=350.0, unit="mm/year", status=ValueStatus.PROVIDED, confidence=1.0)
p_b.biodiversity.pollinator_presence = EnvironmentalMetric[str](value="scarce", status=ValueStatus.PROVIDED)

audit_profile("CASE B (Semi-Arid Wheat Monoculture)", p_b)

# Build Case C
p_c = EnvironmentalProfile()
p_c.location.biome = "tropical_dry_forest"
p_c.location.region_name = "Sub-Tropical Agricultural Margin"
p_c.soil.organic_carbon_percent = EnvironmentalMetric[float](value=0.45, unit="%", status=ValueStatus.PROVIDED, confidence=1.0)
p_c.climate.rainfall_mm_year = EnvironmentalMetric[float](value=420.0, unit="mm/year", status=ValueStatus.PROVIDED, confidence=1.0)
p_c.climate.temperature_mean_c = EnvironmentalMetric[float](value=33.5, unit="°C", status=ValueStatus.PROVIDED, confidence=1.0)
p_c.land.cropping_pattern = EnvironmentalMetric[str](value="monoculture", status=ValueStatus.PROVIDED, confidence=1.0)
p_c.human_impact.deforestation_history = EnvironmentalMetric[str](value="recent", status=ValueStatus.PROVIDED, confidence=1.0)
p_c.human_impact.pollution_level = EnvironmentalMetric[str](value="high", status=ValueStatus.PROVIDED, confidence=1.0)
p_c.human_impact.pollution_types = ["pesticides"]

audit_profile("CASE C (Multi-Stressor Profile)", p_c)

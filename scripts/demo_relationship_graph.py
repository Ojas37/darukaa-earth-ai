import json
from app.schemas.profile import EnvironmentalProfile, ValueStatus, EnvironmentalMetric
from app.reasoning.relationship_graph import relationship_graph

def demonstrate_graph_traversal():
    print("================================================================================")
    print("DARUKAA.EARTH - ENVIRONMENTAL RELATIONSHIP GRAPH TRAVERSAL DEMO")
    print("================================================================================\n")

    # 1. Inspect all 12 defined Causal Edges
    print(f"Total Causal Edges in Knowledge Graph: {len(relationship_graph.edges)}\n")
    print("GRAPH EDGES SPECIFICATION:")
    print("-" * 80)
    for edge in relationship_graph.edges:
        print(f"[{edge.id}] ({edge.strength.value})")
        print(f"  {edge.source_node} --[{edge.effect_direction.value}]--> {edge.target_node}")
        print(f"  Condition: {edge.condition_description}")
        print(f"  Mechanism: {edge.mechanism}\n")

    # 2. Test Case B: Semi-Arid Monoculture Degradation
    print("=" * 80)
    print("CASE B: SEMI-ARID MONOCULTURE WHEAT FARM (Degraded Scenario)")
    print("=" * 80)
    profile_b = EnvironmentalProfile()
    profile_b.location.region_name = "Semi Arid Plateau"
    profile_b.location.biome = "semi_arid"
    profile_b.soil.organic_carbon_percent = EnvironmentalMetric[float](value=0.35, status=ValueStatus.PROVIDED)
    profile_b.land.cropping_pattern = EnvironmentalMetric[str](value="monoculture", status=ValueStatus.PROVIDED)
    profile_b.land.primary_crops = ["wheat"]
    profile_b.climate.rainfall_mm_year = EnvironmentalMetric[float](value=350.0, status=ValueStatus.PROVIDED)

    active_edges = relationship_graph.evaluate_active_edges(profile_b)
    print(f"\nActive Edges Triggered: {len(active_edges)}")
    for e in active_edges:
        print(f"  * {e.source_node} -> {e.target_node} ({e.condition_description})")

    pathways = relationship_graph.find_stress_pathways(profile_b, min_length=2)
    print(f"\nExtracted Multi-Edge Stress Pathways (Chains of Length >= 2): {len(pathways)}\n")
    for p in pathways:
        print(f"[{p.pathway_id}] (Confidence: {p.confidence.value})")
        print(f"  Route: {p.summary}")
        print(f"  Chain Length: {p.chain_length} edges")
        print("  Mechanisms:")
        for idx, edge in enumerate(p.edges, 1):
            print(f"    Step {idx}: {edge.source_node} -> {edge.target_node}")
            print(f"            {edge.mechanism}")
        print()

    # 3. Test Healthy Profile
    print("=" * 80)
    print("CASE HEALTHY: DIVERSIFIED AGROFORESTRY SYSTEM")
    print("=" * 80)
    profile_healthy = EnvironmentalProfile()
    profile_healthy.soil.organic_carbon_percent = EnvironmentalMetric[float](value=3.2, status=ValueStatus.PROVIDED)
    profile_healthy.land.cropping_pattern = EnvironmentalMetric[str](value="agroforestry", status=ValueStatus.PROVIDED)
    profile_healthy.climate.rainfall_mm_year = EnvironmentalMetric[float](value=850.0, status=ValueStatus.PROVIDED)
    profile_healthy.human_impact.pollution_level = EnvironmentalMetric[str](value="none", status=ValueStatus.PROVIDED)
    profile_healthy.human_impact.deforestation_history = EnvironmentalMetric[str](value="none", status=ValueStatus.PROVIDED)

    healthy_pathways = relationship_graph.find_stress_pathways(profile_healthy, min_length=2)
    print(f"Active Stress Pathways for Healthy Profile: {len(healthy_pathways)} (Expected: 0)")

if __name__ == "__main__":
    demonstrate_graph_traversal()

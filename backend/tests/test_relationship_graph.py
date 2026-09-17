import pytest
from app.schemas.profile import (
    EnvironmentalProfile,
    ValueStatus,
    EnvironmentalMetric
)
from app.reasoning.relationship_graph import relationship_graph, EdgeStrength

def test_case_b_profile_triggers_multiple_stress_pathways():
    """
    Case B Profile:
    - Biome: semi_arid
    - SOC: 0.35% (provided)
    - Cropping: monoculture wheat (provided)
    - Rainfall: 350mm/year (provided)
    """
    profile = EnvironmentalProfile()
    profile.location.biome = "semi_arid"
    profile.soil.organic_carbon_percent = EnvironmentalMetric[float](value=0.35, status=ValueStatus.PROVIDED)
    profile.land.cropping_pattern = EnvironmentalMetric[str](value="monoculture", status=ValueStatus.PROVIDED)
    profile.land.primary_crops = ["wheat"]
    profile.climate.rainfall_mm_year = EnvironmentalMetric[float](value=350.0, status=ValueStatus.PROVIDED)

    # 1. Evaluate active edges
    active_edges = relationship_graph.evaluate_active_edges(profile)
    active_edge_ids = [e.id for e in active_edges]

    assert "edge_soc_to_infiltration" in active_edge_ids
    assert "edge_infiltration_to_moisture_stress" in active_edge_ids
    assert "edge_moisture_stress_to_pollinator_food" in active_edge_ids
    assert "edge_food_scarcity_to_pollinator_abundance" in active_edge_ids
    assert "edge_monoculture_to_homogenization" in active_edge_ids
    assert "edge_homogenization_to_species_richness" in active_edge_ids

    # 2. Find stress pathways (chains of length >= 2)
    pathways = relationship_graph.find_stress_pathways(profile, min_length=2)
    assert len(pathways) >= 2

    # Pathway 1: Soil carbon -> Infiltration -> Moisture Stress -> Pollinator food
    soil_water_paths = [p for p in pathways if p.start_variable == "soil.organic_carbon_percent"]
    assert len(soil_water_paths) > 0
    longest_soil_path = max(soil_water_paths, key=lambda p: p.chain_length)
    assert longest_soil_path.chain_length >= 3
    assert "soil.water_infiltration" in longest_soil_path.nodes
    assert "soil.moisture_stress" in longest_soil_path.nodes

    # Pathway 2: Monoculture -> Homogenization -> Species Richness
    monoculture_paths = [p for p in pathways if p.start_variable == "land.cropping_pattern"]
    assert len(monoculture_paths) > 0
    assert any("biodiversity.species_richness" in p.nodes for p in monoculture_paths)

def test_healthy_profile_triggers_zero_stress_pathways():
    """
    Healthy Profile:
    - Biome: temperate
    - SOC: 3.5% (optimal)
    - Cropping: agroforestry / intercropping
    - Rainfall: 800mm/year (healthy)
    - Pollution: none
    - Deforestation: none
    """
    healthy_profile = EnvironmentalProfile()
    healthy_profile.location.biome = "temperate"
    healthy_profile.soil.organic_carbon_percent = EnvironmentalMetric[float](value=3.5, status=ValueStatus.PROVIDED)
    healthy_profile.soil.ph = EnvironmentalMetric[float](value=6.8, status=ValueStatus.PROVIDED)
    healthy_profile.land.cropping_pattern = EnvironmentalMetric[str](value="agroforestry", status=ValueStatus.PROVIDED)
    healthy_profile.climate.rainfall_mm_year = EnvironmentalMetric[float](value=800.0, status=ValueStatus.PROVIDED)
    healthy_profile.human_impact.pollution_level = EnvironmentalMetric[str](value="none", status=ValueStatus.PROVIDED)
    healthy_profile.human_impact.deforestation_history = EnvironmentalMetric[str](value="none", status=ValueStatus.PROVIDED)

    active_edges = relationship_graph.evaluate_active_edges(healthy_profile)
    pathways = relationship_graph.find_stress_pathways(healthy_profile, min_length=2)

    assert len(active_edges) == 0
    assert len(pathways) == 0

def test_pollution_and_deforestation_pathways():
    """
    Verifies that high pollution and recent deforestation trigger their specific causal chains.
    """
    stress_profile = EnvironmentalProfile()
    stress_profile.human_impact.pollution_level = EnvironmentalMetric[str](value="high", status=ValueStatus.PROVIDED)
    stress_profile.human_impact.deforestation_history = EnvironmentalMetric[str](value="recent", status=ValueStatus.PROVIDED)

    pathways = relationship_graph.find_stress_pathways(stress_profile, min_length=2)
    assert len(pathways) >= 2

    # Verify pollution -> toxicity -> species richness
    assert any("biodiversity.non_target_toxicity" in p.nodes for p in pathways)
    # Verify deforestation -> microclimate -> temperature stress
    assert any("climate.microclimate_buffering" in p.nodes for p in pathways)

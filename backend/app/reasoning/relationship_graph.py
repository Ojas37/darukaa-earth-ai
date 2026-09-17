from enum import Enum
from typing import List, Dict, Any, Optional, Set, Callable
from pydantic import BaseModel, Field
from app.schemas.profile import EnvironmentalProfile, ValueStatus

class EdgeStrength(str, Enum):
    ESTABLISHED = "established"
    LIKELY = "likely"
    CONTEXT_DEPENDENT = "context-dependent"

class EffectDirection(str, Enum):
    INCREASES = "increases"
    DECREASES = "decreases"
    DEGRADES = "degrades"
    CONSTRAINS = "constrains"

class CausalEdge(BaseModel):
    id: str
    source_node: str
    target_node: str
    condition_description: str
    effect_direction: EffectDirection
    mechanism: str
    strength: EdgeStrength

class StressPathway(BaseModel):
    pathway_id: str
    start_variable: str
    terminal_variable: str
    nodes: List[str]
    edges: List[CausalEdge]
    chain_length: int
    summary: str
    confidence: EdgeStrength

class RelationshipGraph:
    """
    Explicit ecological relationship graph modeling causal dependencies
    between environmental profile variables and cascading biodiversity stress pathways.
    """

    def __init__(self):
        self.edges: List[CausalEdge] = []
        self._edge_evaluators: Dict[str, Callable[[EnvironmentalProfile, Set[str]], bool]] = {}
        self._build_graph()

    def _add_edge(
        self,
        edge_id: str,
        source_node: str,
        target_node: str,
        condition_description: str,
        effect_direction: EffectDirection,
        mechanism: str,
        strength: EdgeStrength,
        evaluator: Callable[[EnvironmentalProfile, Set[str]], bool]
    ):
        edge = CausalEdge(
            id=edge_id,
            source_node=source_node,
            target_node=target_node,
            condition_description=condition_description,
            effect_direction=effect_direction,
            mechanism=mechanism,
            strength=strength
        )
        self.edges.append(edge)
        self._edge_evaluators[edge_id] = evaluator

    def _build_graph(self):
        """Initializes the 12 explicit causal ecological edges."""

        # -------------------------------------------------------------
        # 1. Low SOC -> Reduced Infiltration
        # -------------------------------------------------------------
        self._add_edge(
            edge_id="edge_soc_to_infiltration",
            source_node="soil.organic_carbon_percent",
            target_node="soil.water_infiltration",
            condition_description="Soil Organic Carbon < 1.0%",
            effect_direction=EffectDirection.DECREASES,
            mechanism="Depleted soil organic carbon destabilizes soil aggregates and collapses macro-pore structure, reducing water infiltration and retention.",
            strength=EdgeStrength.ESTABLISHED,
            evaluator=lambda p, active: (
                p.soil.organic_carbon_percent.is_known and 
                p.soil.organic_carbon_percent.value is not None and 
                p.soil.organic_carbon_percent.value < 1.0
            )
        )

        # -------------------------------------------------------------
        # 2. Reduced Infiltration -> Moisture Stress
        # -------------------------------------------------------------
        self._add_edge(
            edge_id="edge_infiltration_to_moisture_stress",
            source_node="soil.water_infiltration",
            target_node="soil.moisture_stress",
            condition_description="Infiltration degraded under low rainfall (<450mm) or low moisture",
            effect_direction=EffectDirection.INCREASES,
            mechanism="Impaired infiltration combined with low organic matter exacerbates root-zone moisture deficits under low precipitation regimes.",
            strength=EdgeStrength.ESTABLISHED,
            evaluator=lambda p, active: (
                "soil.water_infiltration" in active and (
                    (p.climate.rainfall_mm_year.is_known and p.climate.rainfall_mm_year.value is not None and p.climate.rainfall_mm_year.value < 450.0) or
                    (p.climate.rainfall_pattern.is_known and "low" in str(p.climate.rainfall_pattern.value).lower()) or
                    (p.location.biome in ["semi_arid", "arid"])
                )
            )
        )

        # -------------------------------------------------------------
        # 3. Moisture Stress -> Pollinator Food Scarcity
        # -------------------------------------------------------------
        self._add_edge(
            edge_id="edge_moisture_stress_to_pollinator_food",
            source_node="soil.moisture_stress",
            target_node="biodiversity.pollinator_food_availability",
            condition_description="Rhizosphere moisture stress active",
            effect_direction=EffectDirection.DECREASES,
            mechanism="Severe rhizosphere water deficits reduce vegetative biomass, shorten flowering duration, and suppress nectar and pollen secretion.",
            strength=EdgeStrength.LIKELY,
            evaluator=lambda p, active: "soil.moisture_stress" in active
        )

        # -------------------------------------------------------------
        # 4. Low SOC -> Microbial Diversity Depletion
        # -------------------------------------------------------------
        self._add_edge(
            edge_id="edge_soc_to_microbial_diversity",
            source_node="soil.organic_carbon_percent",
            target_node="biodiversity.soil_microbial_diversity",
            condition_description="Soil Organic Carbon < 1.0%",
            effect_direction=EffectDirection.DECREASES,
            mechanism="Substrate carbon limitation starves heterotrophic bacteria and mycorrhizal fungal networks, suppressing soil biological activity and nutrient mineralization.",
            strength=EdgeStrength.ESTABLISHED,
            evaluator=lambda p, active: (
                p.soil.organic_carbon_percent.is_known and 
                p.soil.organic_carbon_percent.value is not None and 
                p.soil.organic_carbon_percent.value < 1.0
            )
        )

        # -------------------------------------------------------------
        # 5. Monoculture -> Landscape Structural Homogenization
        # -------------------------------------------------------------
        self._add_edge(
            edge_id="edge_monoculture_to_homogenization",
            source_node="land.cropping_pattern",
            target_node="land.habitat_homogenization",
            condition_description="Cropping pattern is monoculture",
            effect_direction=EffectDirection.INCREASES,
            mechanism="Continuous single-crop cultivation eliminates vertical canopy stratigraphy and temporal floral continuity across the landscape.",
            strength=EdgeStrength.ESTABLISHED,
            evaluator=lambda p, active: (
                p.land.cropping_pattern.is_known and 
                str(p.land.cropping_pattern.value).lower() == "monoculture"
            )
        )

        # -------------------------------------------------------------
        # 6. Habitat Homogenization -> Species Richness Decline
        # -------------------------------------------------------------
        self._add_edge(
            edge_id="edge_homogenization_to_species_richness",
            source_node="land.habitat_homogenization",
            target_node="biodiversity.species_richness",
            condition_description="Structural habitat homogenization active",
            effect_direction=EffectDirection.DECREASES,
            mechanism="Homogenized vegetation structure and synchronized harvest cycles eliminate microrefugia, driving systemic declines in indigenous species richness.",
            strength=EdgeStrength.ESTABLISHED,
            evaluator=lambda p, active: "land.habitat_homogenization" in active
        )

        # -------------------------------------------------------------
        # 7. Pollinator Food Scarcity / Homogenization -> Pollinator Abundance Collapse
        # -------------------------------------------------------------
        self._add_edge(
            edge_id="edge_food_scarcity_to_pollinator_abundance",
            source_node="biodiversity.pollinator_food_availability",
            target_node="biodiversity.pollinator_abundance",
            condition_description="Floral food scarcity or habitat homogenization active",
            effect_direction=EffectDirection.DECREASES,
            mechanism="Absence of continuous floral forage and nesting resources causes rapid attrition and local extinction of native wild pollinator populations.",
            strength=EdgeStrength.ESTABLISHED,
            evaluator=lambda p, active: (
                "biodiversity.pollinator_food_availability" in active or 
                "land.habitat_homogenization" in active
            )
        )

        # -------------------------------------------------------------
        # 8. Deforestation -> Microclimate Buffering Loss
        # -------------------------------------------------------------
        self._add_edge(
            edge_id="edge_deforestation_to_microclimate_buffering",
            source_node="human_impact.deforestation_history",
            target_node="climate.microclimate_buffering",
            condition_description="Recent or historic deforestation present",
            effect_direction=EffectDirection.DECREASES,
            mechanism="Loss of tree canopy cover eliminates local evapotranspirative cooling and exposes ground surfaces to direct radiation and wind scouring.",
            strength=EdgeStrength.ESTABLISHED,
            evaluator=lambda p, active: (
                p.human_impact.deforestation_history.is_known and 
                p.human_impact.deforestation_history.value in ["recent", "historic"]
            )
        )

        # -------------------------------------------------------------
        # 9. Microclimate Buffering Loss -> Temperature Stress
        # -------------------------------------------------------------
        self._add_edge(
            edge_id="edge_microclimate_to_temperature_stress",
            source_node="climate.microclimate_buffering",
            target_node="climate.temperature_stress",
            condition_description="Microclimate buffering lost or mean temperature > 32°C",
            effect_direction=EffectDirection.INCREASES,
            mechanism="Unbuffered solar radiation induces extreme soil surface temperature spikes, accelerating moisture vapor loss and heat-stressing organisms.",
            strength=EdgeStrength.LIKELY,
            evaluator=lambda p, active: (
                "climate.microclimate_buffering" in active or (
                    p.climate.temperature_mean_c.is_known and 
                    p.climate.temperature_mean_c.value is not None and 
                    p.climate.temperature_mean_c.value > 32.0
                )
            )
        )

        # -------------------------------------------------------------
        # 10. Agrochemical Pollution -> Non-Target Ecotoxicity
        # -------------------------------------------------------------
        self._add_edge(
            edge_id="edge_pollution_to_toxicity",
            source_node="human_impact.pollution_level",
            target_node="biodiversity.non_target_toxicity",
            condition_description="Pollution level is moderate, high, or severe",
            effect_direction=EffectDirection.INCREASES,
            mechanism="Agrochemical pesticide residues and chemical effluents exert direct lethal and sub-lethal toxicity on non-target beneficial arthropods and mycorrhizae.",
            strength=EdgeStrength.ESTABLISHED,
            evaluator=lambda p, active: (
                p.human_impact.pollution_level.is_known and 
                p.human_impact.pollution_level.value in ["moderate", "high", "severe"]
            )
        )

        # -------------------------------------------------------------
        # 11. Non-Target Ecotoxicity -> Species Richness Decline
        # -------------------------------------------------------------
        self._add_edge(
            edge_id="edge_toxicity_to_species_richness",
            source_node="biodiversity.non_target_toxicity",
            target_node="biodiversity.species_richness",
            condition_description="Non-target ecotoxicity active",
            effect_direction=EffectDirection.DECREASES,
            mechanism="Non-target chemical mortality destabilizes trophic food webs and eliminates natural biological pest controls.",
            strength=EdgeStrength.ESTABLISHED,
            evaluator=lambda p, active: "biodiversity.non_target_toxicity" in active
        )

        # -------------------------------------------------------------
        # 12. Low Rainfall -> Hydrological Constraint
        # -------------------------------------------------------------
        self._add_edge(
            edge_id="edge_rainfall_to_hydrological_constraint",
            source_node="climate.rainfall_mm_year",
            target_node="climate.hydrological_constraint",
            condition_description="Rainfall < 400mm/yr or semi-arid/arid biome",
            effect_direction=EffectDirection.INCREASES,
            mechanism="Chronic atmospheric and precipitation deficits limit natural biomass regeneration and increase susceptibility to secondary land degradation.",
            strength=EdgeStrength.ESTABLISHED,
            evaluator=lambda p, active: (
                (p.climate.rainfall_mm_year.is_known and p.climate.rainfall_mm_year.value is not None and p.climate.rainfall_mm_year.value < 400.0) or
                (p.climate.rainfall_pattern.is_known and "low" in str(p.climate.rainfall_pattern.value).lower()) or
                (p.location.biome in ["semi_arid", "arid"])
            )
        )

    def evaluate_active_edges(self, profile: EnvironmentalProfile) -> List[CausalEdge]:
        """
        Iteratively evaluates all graph edges until a fixed point of active nodes is reached.
        """
        active_nodes: Set[str] = set()
        active_edges: List[CausalEdge] = []

        # Multi-pass evaluation to allow cascading triggers (e.g. SOC -> Infiltration -> Moisture Stress)
        changed = True
        iterations = 0
        max_iterations = 6

        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            for edge in self.edges:
                if edge.id not in [e.id for e in active_edges]:
                    evaluator = self._edge_evaluators[edge.id]
                    if evaluator(profile, active_nodes):
                        active_edges.append(edge)
                        active_nodes.add(edge.source_node)
                        active_nodes.add(edge.target_node)
                        changed = True

        return active_edges

    def find_stress_pathways(self, profile: EnvironmentalProfile, min_length: int = 2) -> List[StressPathway]:
        """
        Traverses the graph to extract multi-edge causal chains (length >= min_length).
        Returns structured StressPathway objects describing the end-to-end stress mechanics.
        """
        active_edges = self.evaluate_active_edges(profile)
        if not active_edges:
            return []

        # Build adjacency mapping for active edges
        adj: Dict[str, List[CausalEdge]] = {}
        for edge in active_edges:
            adj.setdefault(edge.source_node, []).append(edge)

        all_chains: List[List[CausalEdge]] = []

        def dfs(current_node: str, current_path: List[CausalEdge], visited_nodes: Set[str]):
            outgoing = adj.get(current_node, [])
            if not outgoing or all(e.target_node in visited_nodes for e in outgoing):
                if len(current_path) >= min_length:
                    all_chains.append(list(current_path))
                return

            for edge in outgoing:
                if edge.target_node not in visited_nodes:
                    visited_nodes.add(edge.target_node)
                    current_path.append(edge)
                    dfs(edge.target_node, current_path, visited_nodes)
                    current_path.pop()
                    visited_nodes.remove(edge.target_node)

        # Start traversal from every active root node
        start_nodes = set(e.source_node for e in active_edges)
        for start_node in start_nodes:
            dfs(start_node, [], {start_node})

        # Convert chains to StressPathway objects
        pathways: List[StressPathway] = []
        for i, chain in enumerate(all_chains, 1):
            nodes = [chain[0].source_node] + [e.target_node for e in chain]
            
            # Format ascii representation
            chain_str = " -> ".join(nodes)
            
            # Determine overall pathway confidence
            confidences = [e.strength for e in chain]
            pathway_confidence = (
                EdgeStrength.CONTEXT_DEPENDENT if EdgeStrength.CONTEXT_DEPENDENT in confidences
                else EdgeStrength.LIKELY if EdgeStrength.LIKELY in confidences
                else EdgeStrength.ESTABLISHED
            )

            pathway = StressPathway(
                pathway_id=f"pathway_{i:02d}",
                start_variable=chain[0].source_node,
                terminal_variable=chain[-1].target_node,
                nodes=nodes,
                edges=chain,
                chain_length=len(chain),
                summary=chain_str,
                confidence=pathway_confidence
            )
            pathways.append(pathway)

        return pathways

relationship_graph = RelationshipGraph()

from typing import List, Tuple, Optional
from app.schemas.profile import EnvironmentalProfile, ValueStatus
from app.schemas.chat import MissingInfoItem

class ClarificationEngine:
    """
    Identifies missing critical environmental variables needed for grounded ecological reasoning,
    prioritizing at most 2-3 essential follow-up questions.
    """

    # Critical variable definitions: (field_path, category, display_name, reason, priority)
    CRITICAL_VARIABLES = [
        (
            "soil.organic_carbon_percent",
            "soil",
            "Soil Organic Carbon or Soil Health",
            "Needed to evaluate microbiological nutrient cycling and moisture retention capacity.",
            1,
            "What is your approximate soil organic carbon level or soil condition (e.g., degraded, sandy loam, dark organic soil)?"
        ),
        (
            "climate.rainfall_mm_year",
            "climate",
            "Rainfall Regime or Climate Zone",
            "Critical to ensure proposed interventions do not exceed regional hydrological limits (e.g. avoiding water-intensive crops in drylands).",
            2,
            "What is your typical rainfall pattern or regional climate (e.g., semi-arid, low rain <400mm, seasonal monsoon)?"
        ),
        (
            "land.cropping_pattern",
            "land",
            "Cropping Pattern & Land Use",
            "Needed to understand landscape structural diversity, monoculture pressures, and pollinator forage availability.",
            3,
            "Is the land under single-crop monoculture (e.g. wheat only), crop rotation, pasture, or agroforestry?"
        ),
        (
            "soil.ph",
            "soil",
            "Soil pH / Salinity",
            "Needed to evaluate nutrient bioavailability and screen out calcifuge/acid-intolerant cover species.",
            4,
            "Do you have an estimate of the soil pH (e.g., acidic <6, neutral 6.5-7.5, or alkaline/saline >8)?"
        ),
        (
            "human_impact.pollution_level",
            "human_impact",
            "Agrochemical or Pollution Pressures",
            "Helps differentiate chemical ecotoxicity from physical habitat degradation.",
            5,
            "Are chemical pesticides, synthetic fertilizers, or industrial runoff heavily used on or near the site?"
        )
    ]

    def evaluate(self, profile: EnvironmentalProfile) -> Tuple[bool, List[MissingInfoItem], Optional[str]]:
        """
        Evaluates the profile against critical reasoning requirements.
        Returns:
            - needs_clarification: bool
            - missing_items: List[MissingInfoItem] (capped at 2-3 items)
            - clarification_prompt: Optional formatted markdown text
        """
        missing_items: List[MissingInfoItem] = []

        # Check Soil Organic Carbon / Soil Health
        soc_metric = profile.soil.organic_carbon_percent
        texture_metric = profile.soil.texture_class
        soil_known = soc_metric.is_known or (soc_metric.status == ValueStatus.UNKNOWN) or texture_metric.is_known
        if not soil_known:
            missing_items.append(MissingInfoItem(
                field="soil.organic_carbon_percent",
                category="soil",
                question="What is your approximate soil organic carbon or soil quality (e.g., 0.3%, degraded sand, clay loam)?",
                priority=1,
                reason="Determines microbiological nutrient cycling and water infiltration capacity."
            ))

        # Check Climate / Rainfall
        rain_metric = profile.climate.rainfall_mm_year
        pattern_metric = profile.climate.rainfall_pattern
        biome_metric = profile.location.biome
        climate_known = rain_metric.is_known or (rain_metric.status == ValueStatus.UNKNOWN) or pattern_metric.is_known or (biome_metric is not None)
        if not climate_known:
            missing_items.append(MissingInfoItem(
                field="climate.rainfall_mm_year",
                category="climate",
                question="What is your typical rainfall pattern or geographic region (e.g., semi-arid, low rain, temperate)?",
                priority=2,
                reason="Ensures recommended interventions comply with local water availability."
            ))

        # Check Land Use / Cropping Pattern
        crop_metric = profile.land.cropping_pattern
        land_use_metric = profile.land.land_use
        crops_list = profile.land.primary_crops
        land_known = crop_metric.is_known or (crop_metric.status == ValueStatus.UNKNOWN) or land_use_metric.is_known or len(crops_list) > 0
        if not land_known:
            missing_items.append(MissingInfoItem(
                field="land.cropping_pattern",
                category="land",
                question="What is your current land use or cropping pattern (e.g., wheat monoculture, intercropping, pasture)?",
                priority=3,
                reason="Identifies structural habitat diversity and biological pressure points."
            ))

        # If all 3 primary categories have at least some data, no clarification is required
        if len(missing_items) == 0:
            return False, [], None

        # Cap follow-up questions at top 2 or 3 to avoid overwhelming the user
        prioritized_items = sorted(missing_items, key=lambda x: x.priority)[:3]

        # Generate conversational clarification prompt
        prompt_lines = [
            "I can help analyze your ecosystem and diagnose the drivers of biodiversity decline.",
            "To generate scientifically grounded recommendations tailored to your land, could you clarify:",
            ""
        ]
        for i, item in enumerate(prioritized_items, 1):
            prompt_lines.append(f"{i}. **{item.category.title()}**: {item.question}")

        prompt_lines.append("")
        prompt_lines.append("*Note: If you don't have exact numbers, qualitative descriptions (e.g., 'dry sandy soil', 'very little rain') work as well.*")

        clarification_prompt = "\n".join(prompt_lines)
        return True, prioritized_items, clarification_prompt

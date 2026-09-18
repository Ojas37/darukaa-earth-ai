import re
import json
import logging
from typing import Optional, Dict, Any
from app.schemas.profile import (
    EnvironmentalProfile,
    ValueStatus,
    EnvironmentalMetric,
    SoilProfile,
    LandProfile,
    BiodiversityProfile,
    ClimateProfile,
    HumanImpactProfile,
    LocationProfile
)
from app.config import settings

logger = logging.getLogger(__name__)

class EnvironmentalExtractor:
    """
    Extracts structured environmental variables from natural language user input.
    Combines high-precision regex/rule-based extraction with optional Anthropic Claude LLM parsing.
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        self.api_key = anthropic_api_key or settings.anthropic_api_key
        self.client = None
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")

    def extract(self, text: str, existing_profile: Optional[EnvironmentalProfile] = None) -> EnvironmentalProfile:
        """
        Extracts an EnvironmentalProfile from input text, merging with existing profile if provided.
        """
        # 1. Rule-based deterministic extraction
        extracted_profile = self._rule_based_extract(text)

        # 2. LLM extraction if client available
        if self.client:
            try:
                llm_profile = self._llm_extract(text)
                extracted_profile = extracted_profile.merge_with(llm_profile)
            except Exception as e:
                logger.warning(f"LLM extraction fallback to rule-based: {e}")

        # 3. Merge with existing profile if present
        if existing_profile:
            final_profile = existing_profile.model_copy(deep=True)
            final_profile.merge_with(extracted_profile)
            return final_profile

        return extracted_profile

    def _rule_based_extract(self, text: str) -> EnvironmentalProfile:
        """
        Deterministic extraction using clause-scoped regex and domain patterns.
        """
        profile = EnvironmentalProfile()
        text_lower = text.lower()

        # -----------------------------
        # 1. Location & Biome
        # -----------------------------
        biome_patterns = {
            "semi_arid": [r"semi-arid", r"semi arid", r"dryland", r"dry plateau"],
            "arid": [r"\barid\b", r"desert"],
            "tropical_dry": [r"tropical dry", r"dry deciduous", r"tropical monsoon", r"\bmonsoon\b"],
            "tropical_humid": [r"tropical rainforest", r"humid tropics", r"wet tropics", r"sub-humid", r"subhumid"],
            "temperate": [r"temperate", r"prairie", r"pampas", r"midwest"],
            "mediterranean": [r"mediterranean", r"chaparral"]
        }
        for biome, patterns in biome_patterns.items():
            if any(re.search(pat, text_lower) for pat in patterns):
                profile.location.biome = biome
                profile.location.region_name = biome.replace("_", " ").title()
                break

        # Check for specific geographic region mentions
        region_match = re.search(r"(?:located in|in the region of|in|from|region of)\s+([A-Za-z0-9\s\-]+?)(?:,|\.|\band\b|with|$)", text, re.IGNORECASE)
        if region_match and not profile.location.region_name:
            reg = region_match.group(1).strip()
            excluded_words = [
                "low", "high", "percent", "crop", "erosion", "suffer", "degrad",
                "nutrient", "runoff", "drought", "matter", "carbon", "loss",
                "monsoon", "rain", "soil", "extreme", "depletion", "heavy",
                "clay", "sand", "loam", "poor", "acid", "saline"
            ]
            if len(reg) < 30 and not any(k in reg.lower() for k in excluded_words):
                profile.location.region_name = reg

        # -----------------------------
        # 2. Soil Organic Carbon (SOC) / Soil Organic Matter (SOM)
        # -----------------------------
        # Clause-scoped unknown check
        if re.search(r"(?:don'?t know|no idea|unknown|not sure|haven'?t tested)[^.,;\n]*(?:carbon|soc|organic matter|som)", text_lower):
            profile.soil.organic_carbon_percent.status = ValueStatus.UNKNOWN
        else:
            # SOC/SOM percentage: e.g. "soil carbon is 0.3%", "organic matter at 0.4%", "SOC 0.35%", "SOM: 1.2%"
            soc_match = re.search(r"(?:soil\s+organic\s+carbon|organic\s+carbon|soil\s+carbon|soil\s+organic\s+matter|organic\s+matter|carbon|soc|som)[\s:=a-z]*(?:is|of|=|around|approx(?:imately)?|at|about)?\s*([0-9]+(?:\.[0-9]+)?)\s*%", text_lower)
            if not soc_match:
                # E.g. "0.3% soil carbon" or "0.4% organic matter" or "0.3% SOC"
                soc_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%\s*(?:soil\s+organic\s+carbon|soil\s+carbon|organic\s+carbon|soil\s+organic\s+matter|organic\s+matter|carbon|soc|som)", text_lower)
            if not soc_match:
                # Direct percentage after carbon/matter mention
                soc_match = re.search(r"(?:soil\s+carbon|organic\s+matter|carbon|soc|som)[^\d%]{1,20}([0-9]+(?:\.[0-9]+)?)\s*%", text_lower)

            if soc_match:
                val = float(soc_match.group(1))
                if 0.0 <= val <= 100.0:
                    profile.soil.organic_carbon_percent = EnvironmentalMetric[float](
                        value=val,
                        unit="%",
                        status=ValueStatus.PROVIDED,
                        confidence=1.0,
                        raw_input=soc_match.group(0)
                    )
            elif any(k in text_lower for k in ["low carbon", "poor soil carbon", "depleted carbon", "low soc", "low organic matter", "depleted organic matter"]):
                profile.soil.organic_carbon_percent = EnvironmentalMetric[float](
                    value=0.5,
                    unit="%",
                    status=ValueStatus.ESTIMATED,
                    confidence=0.7,
                    source_notes="Estimated from qualitative 'low carbon/organic matter' description"
                )

        # -----------------------------
        # 3. Soil pH
        # -----------------------------
        if re.search(r"(?:don'?t know|no idea|unknown|not sure|haven'?t tested)[^.,;\n]*(?:ph|acidity|alkalinity)", text_lower):
            profile.soil.ph.status = ValueStatus.UNKNOWN
        else:
            ph_match = re.search(r"(?:soil\s+)?ph[\s:=a-z]*(?:is|=|of|around|at|about)?\s*([0-9]+(?:\.[0-9]+)?)", text_lower)
            if ph_match:
                val = float(ph_match.group(1))
                if 0.0 <= val <= 14.0:
                    profile.soil.ph = EnvironmentalMetric[float](
                        value=val,
                        unit="pH",
                        status=ValueStatus.PROVIDED,
                        confidence=1.0,
                        raw_input=ph_match.group(0)
                    )
            elif "acidic" in text_lower or "acid soil" in text_lower:
                profile.soil.ph = EnvironmentalMetric[float](
                    value=5.2,
                    unit="pH",
                    status=ValueStatus.ESTIMATED,
                    confidence=0.7,
                    source_notes="Estimated from 'acidic soil'"
                )
            elif "alkaline" in text_lower or "saline" in text_lower or "sodic" in text_lower:
                profile.soil.ph = EnvironmentalMetric[float](
                    value=8.3,
                    unit="pH",
                    status=ValueStatus.ESTIMATED,
                    confidence=0.7,
                    source_notes="Estimated from 'alkaline/saline soil'"
                )

        # -----------------------------
        # 4. Soil Texture
        # -----------------------------
        textures = ["sandy loam", "clay loam", "silty clay", "sand", "clay", "loam", "silt", "gravel"]
        for tex in textures:
            if re.search(rf"\b{tex}\b", text_lower):
                profile.soil.texture_class = EnvironmentalMetric[str](
                    value=tex,
                    status=ValueStatus.PROVIDED,
                    confidence=1.0
                )
                break

        # -----------------------------
        # 5. Cropping Pattern & Crops
        # -----------------------------
        if "monoculture" in text_lower or "single crop" in text_lower or "only grow" in text_lower or "grow only" in text_lower or "sole crop" in text_lower:
            profile.land.cropping_pattern = EnvironmentalMetric[str](
                value="monoculture",
                status=ValueStatus.PROVIDED,
                confidence=1.0
            )
        elif "intercrop" in text_lower or "inter-cropping" in text_lower:
            profile.land.cropping_pattern = EnvironmentalMetric[str](
                value="intercropping",
                status=ValueStatus.PROVIDED,
                confidence=1.0
            )
        elif "agroforestry" in text_lower:
            profile.land.cropping_pattern = EnvironmentalMetric[str](
                value="agroforestry",
                status=ValueStatus.PROVIDED,
                confidence=1.0
            )
        elif "crop rotation" in text_lower or "rotating crops" in text_lower:
            profile.land.cropping_pattern = EnvironmentalMetric[str](
                value="crop_rotation",
                status=ValueStatus.PROVIDED,
                confidence=1.0
            )

        # Land use & Land cover
        if "riparian" in text_lower or "riverbank" in text_lower or "stream bank" in text_lower or "buffer zone" in text_lower:
            profile.land.land_cover = EnvironmentalMetric[str](value="riparian_buffer", status=ValueStatus.PROVIDED)
            if not profile.land.land_use.is_known:
                profile.land.land_use = EnvironmentalMetric[str](value="riparian_corridor", status=ValueStatus.PROVIDED)

        if "pasture" in text_lower or "grazing" in text_lower:
            profile.land.land_use = EnvironmentalMetric[str](value="pasture", status=ValueStatus.PROVIDED)
        elif any(k in text_lower for k in ["farm", "cropland", "crop", "hectares", "acres", "field"]):
            if not profile.land.land_use.is_known:
                profile.land.land_use = EnvironmentalMetric[str](value="cropland", status=ValueStatus.PROVIDED)

        # Primary Crops
        common_crops = ["wheat", "corn", "maize", "soybean", "soy", "cotton", "rice", "barley", "canola", "sunflower", "coffee", "millet", "sorghum"]
        for crop in common_crops:
            if re.search(rf"\b{crop}\b", text_lower):
                profile.land.primary_crops.append(crop)

        # -----------------------------
        # 6. Climate & Rainfall
        # -----------------------------
        if re.search(r"(?:don'?t know|no idea|unknown|not sure|haven'?t checked)[^.,;\n]*(?:rain|rainfall|precipitation)", text_lower):
            profile.climate.rainfall_mm_year.status = ValueStatus.UNKNOWN
        else:
            # Numerical rainfall (mm/year or inches/year)
            rain_mm = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:mm|millimeters)(?:/(?:yr|year))?", text_lower)
            rain_in = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:inches|in)(?:/(?:yr|year))?", text_lower)
            
            if rain_mm:
                val = float(rain_mm.group(1))
                profile.climate.rainfall_mm_year = EnvironmentalMetric[float](
                    value=val,
                    unit="mm/year",
                    status=ValueStatus.PROVIDED,
                    confidence=1.0
                )
            elif rain_in:
                val_mm = round(float(rain_in.group(1)) * 25.4, 1)
                profile.climate.rainfall_mm_year = EnvironmentalMetric[float](
                    value=val_mm,
                    unit="mm/year",
                    status=ValueStatus.PROVIDED,
                    confidence=1.0,
                    source_notes=f"Converted from {rain_in.group(1)} inches"
                )
            elif any(k in text_lower for k in ["low rain", "very little rain", "drought", "scanty rain", "infrequent rain", "low rainfall"]):
                profile.climate.rainfall_pattern = EnvironmentalMetric[str](
                    value="low_rainfall_semi_arid",
                    status=ValueStatus.PROVIDED
                )
                if not profile.climate.rainfall_mm_year.is_known:
                    profile.climate.rainfall_mm_year = EnvironmentalMetric[float](
                        value=350.0,
                        unit="mm/year",
                        status=ValueStatus.ESTIMATED,
                        confidence=0.7,
                        source_notes="Estimated from 'low rainfall/drought' description"
                    )

        # -----------------------------
        # 7. Biodiversity Indicators
        # -----------------------------
        if any(k in text_lower for k in ["pollinator", "bee", "butterfly", "insects"]):
            if any(k in text_lower for k in ["decline", "declining", "dropped", "plummet", "disappeared", "scarce", "few", "low", "lost", "worse"]):
                profile.biodiversity.pollinator_presence = EnvironmentalMetric[str](
                    value="scarce",
                    status=ValueStatus.PROVIDED
                )
                profile.biodiversity.observed_issues.append("pollinator_decline")

        if any(k in text_lower for k in ["biodiversity is declining", "biodiversity loss", "declining biodiversity", "biodiversity is getting worse", "species disappearing", "biodiversity declining", "biodiversity dropped", "biodiversity has dropped"]):
            profile.biodiversity.species_richness = EnvironmentalMetric[str](
                value="declining",
                status=ValueStatus.PROVIDED
            )
            profile.biodiversity.observed_issues.append("biodiversity_decline")

        # Invasive species and native vegetation suppression detection
        if any(k in text_lower for k in ["invasive", "weed species", "choking native", "invasive species", "alien plant", "choking"]):
            if "invasive_species_dominance" not in profile.biodiversity.observed_issues:
                profile.biodiversity.observed_issues.append("invasive_species_dominance")
            if any(k in text_lower for k in ["choking", "suppress", "lost", "kill", "displace", "outcompet"]):
                if "native_vegetation_suppression" not in profile.biodiversity.observed_issues:
                    profile.biodiversity.observed_issues.append("native_vegetation_suppression")
            if not profile.biodiversity.species_richness.is_known:
                profile.biodiversity.species_richness = EnvironmentalMetric[str](
                    value="declining",
                    status=ValueStatus.PROVIDED
                )

        # Riverbank slope instability / root cohesion loss
        if any(k in text_lower for k in ["slope instability", "bank instability", "riverbank slope", "bank erosion", "poor root cohesion", "bank failure", "slope failure"]):
            if "bank_instability" not in profile.biodiversity.observed_issues:
                profile.biodiversity.observed_issues.append("bank_instability")
            if "poor root cohesion" in text_lower or "root cohesion" in text_lower:
                if "poor_root_cohesion" not in profile.biodiversity.observed_issues:
                    profile.biodiversity.observed_issues.append("poor_root_cohesion")

        # Soil biological activity (earthworms, microbes, mycorrhizae) detection
        _soil_biology_keywords = [
            "earthworm", "earth worm", "worm population", "worms have vanished",
            "worms disappeared", "no worms", "loss of worms", "worm decline",
            "soil fauna", "soil macrofauna", "macrofauna", "soil invertebrate",
            "soil organism", "belowground fauna", "annelid",
            "microbial", "microbe", "microbiome", "mycorrhiz", "microbial biomass",
            "soil biology", "biological activity",
        ]
        _soil_biology_negative_keywords = [
            "vanish", "disappear", "decline", "lost", "absent", "gone",
            "collapse", "drop", "reduced", "low", "scarce", "no ",
            "deplet", "depletion",
        ]
        if any(k in text_lower for k in _soil_biology_keywords):
            # Only mark as degraded if a loss/absence/depletion signal is also present
            if any(k in text_lower for k in _soil_biology_negative_keywords):
                profile.biodiversity.soil_biological_activity = EnvironmentalMetric[str](
                    value="low",
                    status=ValueStatus.PROVIDED,
                    raw_input="soil fauna/microbial depletion detected"
                )
                if "soil_biological_depletion" not in profile.biodiversity.observed_issues:
                    profile.biodiversity.observed_issues.append("soil_biological_depletion")
            else:
                if "soil_biology_noted" not in profile.biodiversity.observed_issues:
                    profile.biodiversity.observed_issues.append("soil_biology_noted")

        # -----------------------------
        # 8. Human Impact (Pollution & Deforestation)
        # -----------------------------
        # Nitrate / agricultural nutrient runoff detection
        if any(k in text_lower for k in ["nitrate", "nitrogen runoff", "phosphate", "nutrient runoff", "nitrate runoff", "45 mg/l", "mg/l nitrate"]):
            profile.human_impact.pollution_level = EnvironmentalMetric[str](
                value="high" if any(k in text_lower for k in ["45 mg", "high nitrate", "heavy nitrate", "severe nitrate"]) else "moderate",
                status=ValueStatus.PROVIDED
            )
            if "nitrate_runoff" not in profile.human_impact.pollution_types:
                profile.human_impact.pollution_types.append("nitrate_runoff")
            if "excess_nutrients" not in profile.human_impact.pollution_types:
                profile.human_impact.pollution_types.append("excess_nutrients")
            if "nitrate_pollution" not in profile.biodiversity.observed_issues:
                profile.biodiversity.observed_issues.append("nitrate_pollution")

        # Agrochemical keywords — glyphosate/herbicides always set high pollution
        _high_pollution_keywords = [
            "glyphosate", "roundup", "atrazine", "2,4-d", "paraquat",
            "chlorpyrifos", "neonicotinoid", "imidacloprid", "fungicide",
            "insecticide", "agrochemical", "agrichemical",
            "heavy pesticide", "intensive pesticide", "frequent pesticide",
            "heavy chemical", "intensive chemical", "frequent chemical application",
            "heavy herbicide", "frequent herbicide",
        ]
        _moderate_pollution_keywords = [
            "pesticide", "herbicide", "chemical pollution", "pesticide runoff",
            "chemical runoff", "toxic runoff", "fertilizer pollution", "severe chemical",
            "spraying chemicals", "synthetic pesticide", "toxic spray",
        ]

        if any(k in text_lower for k in _high_pollution_keywords):
            profile.human_impact.pollution_level = EnvironmentalMetric[str](
                value="high",
                status=ValueStatus.PROVIDED
            )
            # Detect specific types
            if any(k in text_lower for k in ["glyphosate", "roundup", "herbicide", "2,4-d", "atrazine", "paraquat"]):
                if "herbicides" not in profile.human_impact.pollution_types:
                    profile.human_impact.pollution_types.append("herbicides")
            if any(k in text_lower for k in ["insecticide", "neonicotinoid", "imidacloprid", "chlorpyrifos"]):
                if "insecticides" not in profile.human_impact.pollution_types:
                    profile.human_impact.pollution_types.append("insecticides")
            if any(k in text_lower for k in ["fungicide"]):
                if "fungicides" not in profile.human_impact.pollution_types:
                    profile.human_impact.pollution_types.append("fungicides")
            if "glyphosate" in text_lower or "roundup" in text_lower:
                if "glyphosate" not in profile.human_impact.pollution_types:
                    profile.human_impact.pollution_types.append("glyphosate")

        elif any(k in text_lower for k in _moderate_pollution_keywords):
            if not profile.human_impact.pollution_level.is_known:
                profile.human_impact.pollution_level = EnvironmentalMetric[str](
                    value="high" if ("heavy" in text_lower or "intensive" in text_lower or "frequent" in text_lower) else "moderate",
                    status=ValueStatus.PROVIDED
                )
            if "pesticide" in text_lower and "pesticides" not in profile.human_impact.pollution_types:
                profile.human_impact.pollution_types.append("pesticides")
            if "fertilizer" in text_lower and "synthetic_fertilizer" not in profile.human_impact.pollution_types:
                profile.human_impact.pollution_types.append("synthetic_fertilizer")

        if any(k in text_lower for k in ["deforest", "cleared trees", "logging", "cleared forest"]):
            profile.human_impact.deforestation_history = EnvironmentalMetric[str](
                value="recent" if "recent" in text_lower else "historic",
                status=ValueStatus.PROVIDED
            )

        return profile

    def _llm_extract(self, text: str) -> EnvironmentalProfile:
        """
        Uses Anthropic Claude to extract structured environmental metrics in JSON format.
        """
        prompt = f"""You are an environmental data extraction engine for Darukaa.Earth.
Extract structured environmental variables from the following user text.

User Text:
"{text}"

Return ONLY a valid JSON object matching this exact schema:
{{
  "location": {{
    "region_name": string or null,
    "biome": "semi_arid" | "arid" | "tropical_dry" | "tropical_humid" | "temperate" | "mediterranean" | null
  }},
  "soil": {{
    "ph": {{"value": float or null, "status": "provided" | "estimated" | "unknown" | "missing"}},
    "organic_carbon_percent": {{"value": float or null, "status": "provided" | "estimated" | "unknown" | "missing"}},
    "moisture_percent": {{"value": float or null, "status": "provided" | "estimated" | "unknown" | "missing"}},
    "texture_class": {{"value": string or null, "status": "provided" | "estimated" | "unknown" | "missing"}}
  }},
  "land": {{
    "land_use": {{"value": string or null, "status": "provided" | "estimated" | "unknown" | "missing"}},
    "cropping_pattern": {{"value": "monoculture" | "intercropping" | "agroforestry" | "crop_rotation" | null, "status": "provided" | "estimated" | "unknown" | "missing"}},
    "primary_crops": [string]
  }},
  "climate": {{
    "rainfall_mm_year": {{"value": float or null, "status": "provided" | "estimated" | "unknown" | "missing"}},
    "rainfall_pattern": {{"value": string or null, "status": "provided" | "estimated" | "unknown" | "missing"}}
  }},
  "biodiversity": {{
    "pollinator_presence": {{"value": "scarce" | "moderate" | "abundant" | null, "status": "provided" | "estimated" | "unknown" | "missing"}},
    "observed_issues": [string]
  }},
  "human_impact": {{
    "pollution_level": {{"value": "none" | "low" | "moderate" | "high" | "severe" | null, "status": "provided" | "estimated" | "unknown" | "missing"}},
    "deforestation_history": {{"value": string or null, "status": "provided" | "estimated" | "unknown" | "missing"}}
  }}
}}

Rules:
- If a value is not mentioned, mark its status as "missing" with value null.
- If the user explicitly says they do not know a value, mark status as "unknown" with value null.
- If the user provides a number or specific description, mark status as "provided".
- Output raw JSON only with NO markdown fences, no explanatory text.
"""
        response = self.client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1000,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        if not response.content or not hasattr(response.content[0], "text") or not response.content[0].text:
            raise RuntimeError(f"Anthropic returned empty content (stop_reason={response.stop_reason!r}). Falling back to rule-based extraction.")
        content = response.content[0].text.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        data = json.loads(content)
        return EnvironmentalProfile.model_validate(data)

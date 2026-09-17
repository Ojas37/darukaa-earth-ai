from enum import Enum
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, field_validator

class ValueStatus(str, Enum):
    PROVIDED = "provided"      # Explicitly stated by the user or hardware measurements
    ESTIMATED = "estimated"    # Inferred from regional / biome / proxy defaults
    UNKNOWN = "unknown"        # User explicitly stated they do not know the value
    MISSING = "missing"        # Not yet mentioned or evaluated

T = TypeVar("T")

class EnvironmentalMetric(BaseModel, Generic[T]):
    value: Optional[T] = None
    unit: Optional[str] = None
    status: ValueStatus = ValueStatus.MISSING
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    raw_input: Optional[str] = None
    source_notes: Optional[str] = None

    @property
    def is_known(self) -> bool:
        """Returns True if the value is explicitly provided or estimated."""
        return self.status in [ValueStatus.PROVIDED, ValueStatus.ESTIMATED] and self.value is not None

class SoilProfile(BaseModel):
    ph: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="pH"))
    organic_carbon_percent: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="%"))
    moisture_percent: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="%"))
    bulk_density_g_cm3: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="g/cm3"))
    texture_class: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())

    @field_validator("ph")
    @classmethod
    def validate_ph(cls, v: EnvironmentalMetric[float]) -> EnvironmentalMetric[float]:
        if v.value is not None and (v.value < 0.0 or v.value > 14.0):
            raise ValueError(f"Soil pH {v.value} must be within range 0.0 to 14.0")
        return v

    @field_validator("organic_carbon_percent", "moisture_percent")
    @classmethod
    def validate_percentages(cls, v: EnvironmentalMetric[float]) -> EnvironmentalMetric[float]:
        if v.value is not None and (v.value < 0.0 or v.value > 100.0):
            raise ValueError(f"Percentage metric value {v.value} must be within range 0.0 to 100.0")
        return v

class LandProfile(BaseModel):
    land_use: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    land_cover: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    cropping_pattern: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    primary_crops: List[str] = Field(default_factory=list)
    tillage_practice: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    canopy_cover_percent: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="%"))

class BiodiversityProfile(BaseModel):
    species_richness: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    habitat_diversity: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    pollinator_presence: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    soil_biological_activity: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    observed_issues: List[str] = Field(default_factory=list)

class ClimateProfile(BaseModel):
    rainfall_mm_year: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="mm/year"))
    rainfall_pattern: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    temperature_mean_c: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="°C"))
    aridity_index: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float]())

    @field_validator("rainfall_mm_year")
    @classmethod
    def validate_rainfall(cls, v: EnvironmentalMetric[float]) -> EnvironmentalMetric[float]:
        if v.value is not None and v.value < 0.0:
            raise ValueError(f"Rainfall {v.value} cannot be negative")
        return v

class HumanImpactProfile(BaseModel):
    pollution_level: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    pollution_types: List[str] = Field(default_factory=list)
    deforestation_history: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    habitat_fragmentation: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())

class LocationProfile(BaseModel):
    region_name: Optional[str] = None
    biome: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    elevation_m: Optional[float] = None

class EnvironmentalProfile(BaseModel):
    profile_id: str = Field(default_factory=lambda: f"prof_{uuid.uuid4().hex[:10]}")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    location: LocationProfile = Field(default_factory=LocationProfile)
    soil: SoilProfile = Field(default_factory=SoilProfile)
    land: LandProfile = Field(default_factory=LandProfile)
    biodiversity: BiodiversityProfile = Field(default_factory=BiodiversityProfile)
    climate: ClimateProfile = Field(default_factory=ClimateProfile)
    human_impact: HumanImpactProfile = Field(default_factory=HumanImpactProfile)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def merge_with(self, incoming: "EnvironmentalProfile") -> "EnvironmentalProfile":
        """
        Merges an incoming partial profile into this profile.
        Explicitly provided or estimated incoming values override missing/unknown values.
        """
        self.updated_at = datetime.utcnow().isoformat()
        
        # Location merge
        if incoming.location.region_name:
            self.location.region_name = incoming.location.region_name
        if incoming.location.biome:
            self.location.biome = incoming.location.biome
        if incoming.location.latitude is not None:
            self.location.latitude = incoming.location.latitude
        if incoming.location.longitude is not None:
            self.location.longitude = incoming.location.longitude
        if incoming.location.elevation_m is not None:
            self.location.elevation_m = incoming.location.elevation_m

        # Helper for metric merging
        def merge_metric(existing: EnvironmentalMetric, incoming_m: EnvironmentalMetric):
            if incoming_m.status != ValueStatus.MISSING:
                if incoming_m.value is not None or incoming_m.status == ValueStatus.UNKNOWN:
                    existing.value = incoming_m.value
                    existing.status = incoming_m.status
                    if incoming_m.unit:
                        existing.unit = incoming_m.unit
                    if incoming_m.confidence is not None:
                        existing.confidence = incoming_m.confidence
                    if incoming_m.raw_input:
                        existing.raw_input = incoming_m.raw_input
                    if incoming_m.source_notes:
                        existing.source_notes = incoming_m.source_notes

        # Soil
        merge_metric(self.soil.ph, incoming.soil.ph)
        merge_metric(self.soil.organic_carbon_percent, incoming.soil.organic_carbon_percent)
        merge_metric(self.soil.moisture_percent, incoming.soil.moisture_percent)
        merge_metric(self.soil.bulk_density_g_cm3, incoming.soil.bulk_density_g_cm3)
        merge_metric(self.soil.texture_class, incoming.soil.texture_class)

        # Land
        merge_metric(self.land.land_use, incoming.land.land_use)
        merge_metric(self.land.land_cover, incoming.land.land_cover)
        merge_metric(self.land.cropping_pattern, incoming.land.cropping_pattern)
        merge_metric(self.land.tillage_practice, incoming.land.tillage_practice)
        merge_metric(self.land.canopy_cover_percent, incoming.land.canopy_cover_percent)
        if incoming.land.primary_crops:
            self.land.primary_crops = list(set(self.land.primary_crops + incoming.land.primary_crops))

        # Biodiversity
        merge_metric(self.biodiversity.species_richness, incoming.biodiversity.species_richness)
        merge_metric(self.biodiversity.habitat_diversity, incoming.biodiversity.habitat_diversity)
        merge_metric(self.biodiversity.pollinator_presence, incoming.biodiversity.pollinator_presence)
        merge_metric(self.biodiversity.soil_biological_activity, incoming.biodiversity.soil_biological_activity)
        if incoming.biodiversity.observed_issues:
            self.biodiversity.observed_issues = list(set(self.biodiversity.observed_issues + incoming.biodiversity.observed_issues))

        # Climate
        merge_metric(self.climate.rainfall_mm_year, incoming.climate.rainfall_mm_year)
        merge_metric(self.climate.rainfall_pattern, incoming.climate.rainfall_pattern)
        merge_metric(self.climate.temperature_mean_c, incoming.climate.temperature_mean_c)
        merge_metric(self.climate.aridity_index, incoming.climate.aridity_index)

        # Human Impact
        merge_metric(self.human_impact.pollution_level, incoming.human_impact.pollution_level)
        merge_metric(self.human_impact.deforestation_history, incoming.human_impact.deforestation_history)
        merge_metric(self.human_impact.habitat_fragmentation, incoming.human_impact.habitat_fragmentation)
        if incoming.human_impact.pollution_types:
            self.human_impact.pollution_types = list(set(self.human_impact.pollution_types + incoming.human_impact.pollution_types))

        # Metadata
        self.metadata.update(incoming.metadata)
        return self

    def to_summary_dict(self) -> Dict[str, Any]:
        """Returns a concise key-value summary of known/estimated metrics."""
        summary = {}
        if self.location.region_name:
            summary["region"] = self.location.region_name
        if self.location.biome:
            summary["biome"] = self.location.biome

        # Soil
        if self.soil.organic_carbon_percent.is_known:
            summary["soil_organic_carbon"] = f"{self.soil.organic_carbon_percent.value}% ({self.soil.organic_carbon_percent.status.value})"
        if self.soil.ph.is_known:
            summary["soil_ph"] = f"{self.soil.ph.value} ({self.soil.ph.status.value})"
        if self.soil.moisture_percent.is_known:
            summary["soil_moisture"] = f"{self.soil.moisture_percent.value}% ({self.soil.moisture_percent.status.value})"
        if self.soil.texture_class.is_known:
            summary["soil_texture"] = f"{self.soil.texture_class.value}"

        # Land
        if self.land.cropping_pattern.is_known:
            summary["cropping_pattern"] = f"{self.land.cropping_pattern.value}"
        if self.land.primary_crops:
            summary["primary_crops"] = ", ".join(self.land.primary_crops)
        if self.land.land_use.is_known:
            summary["land_use"] = f"{self.land.land_use.value}"

        # Climate
        if self.climate.rainfall_mm_year.is_known:
            summary["rainfall"] = f"{self.climate.rainfall_mm_year.value} mm/yr"
        elif self.climate.rainfall_pattern.is_known:
            summary["rainfall_pattern"] = f"{self.climate.rainfall_pattern.value}"

        # Biodiversity
        if self.biodiversity.pollinator_presence.is_known:
            summary["pollinators"] = f"{self.biodiversity.pollinator_presence.value}"
        if self.biodiversity.observed_issues:
            summary["reported_issues"] = ", ".join(self.biodiversity.observed_issues)

        # Human Impact
        if self.human_impact.pollution_level.is_known:
            summary["pollution"] = f"{self.human_impact.pollution_level.value}"
        if self.human_impact.deforestation_history.is_known:
            summary["deforestation"] = f"{self.human_impact.deforestation_history.value}"

        return summary

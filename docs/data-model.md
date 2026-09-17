# Environmental Data Model Specification — Darukaa.Earth

## 1. Design Principles

1. **Explicit Value States**: A measurement is never simply `null` or silently defaulted. Every variable tracks its provenance and state (`PROVIDED`, `ESTIMATED`, `UNKNOWN`, `MISSING`).
2. **Standardized Scientific Units**: All numerical metrics are normalized to canonical SI or standard ecological units upon ingestion.
3. **Partial Information Resilience**: The system must operate meaningfully on minimal input (e.g., only Soil Organic Carbon and Rainfall known), while acknowledging uncertainty.
4. **Range & Boundary Validation**: Strict physical bounds prevent impossible values (e.g., pH outside 0–14, negative rainfall, or SOC > 100%).

---

## 2. Value Provenance & Status Taxonomy

Each environmental property wraps a value and a `ValueStatus` metadata tag:

```python
from enum import Enum
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, Field

class ValueStatus(str, Enum):
    PROVIDED = "provided"      # Explicitly stated by the user or measured by hardware sensors
    ESTIMATED = "estimated"    # Inferred from regional/biome baseline data
    UNKNOWN = "unknown"        # User explicitly stated they do not know the value
    MISSING = "missing"        # Not yet asked or mentioned in conversation

T = TypeVar("T")

class EnvironmentalMetric(BaseModel, Generic[T]):
    value: Optional[T] = None
    unit: Optional[str] = None
    status: ValueStatus = ValueStatus.MISSING
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    source_notes: Optional[str] = None
```

---

## 3. Core Environmental Variables Specification

### 3.1 Soil Layer (`SoilProfile`)
| Variable | Type | Canonical Unit | Valid Range | Ecological Baseline / Reference |
|---|---|---|---|---|
| `ph` | `float` | pH scale | `0.0 - 14.0` | `<5.5` (acidic stress), `6.0-7.5` (optimal), `>8.2` (saline/sodic) |
| `organic_carbon_percent` | `float` | `%` (SOC) | `0.0 - 100.0` | `<1.0%` (degraded), `1.0-2.5%` (moderate), `>3.0%` (healthy) |
| `moisture_percent` | `float` | `%` vol. | `0.0 - 100.0` | `<15%` (water stress), `20-40%` (field capacity for loams) |
| `texture_class` | `str` | USDA class | categorical | Sand, Sandy Loam, Loam, Silt, Clay, Clay Loam |
| `bulk_density` | `float` | `g/cm³` | `0.5 - 2.5` | `>1.6 g/cm³` (severe compaction restricting root growth) |

### 3.2 Land & Agricultural Layer (`LandProfile`)
| Variable | Type | Canonical Unit | Valid Options / Range | Ecological Significance |
|---|---|---|---|---|
| `land_use` | `str` | categorical | `cropland`, `pasture`, `forest`, `degraded_land`, `urban_edge`, `wetland` | Primary landscape classification |
| `land_cover` | `str` | categorical | `bare_soil`, `annual_crop`, `perennial_crop`, `tree_cover`, `grassland` | Ground protection against erosion |
| `cropping_pattern` | `str` | categorical | `monoculture`, `intercropping`, `crop_rotation`, `agroforestry`, `fallow` | Key driver of biological and structural diversity |
| `canopy_cover_percent`| `float` | `%` | `0.0 - 100.0` | Microclimate buffer and shade regulation |
| `tillage_practice` | `str` | categorical | `conventional_deep`, `minimum_till`, `no_till`, `zero_till` | Direct influence on soil fungal networks & SOC |

### 3.3 Biodiversity & Ecological Health Layer (`BiodiversityProfile`)
| Variable | Type | Canonical Unit | Valid Range | Ecological Significance |
|---|---|---|---|---|
| `species_richness` | `int` | count / area | `≥ 0` | Total number of distinct biological taxa observed |
| `habitat_diversity` | `str` / `float` | categorical / Index | `low`, `moderate`, `high` / `0.0 - 5.0` | Structural complexity and microhabitat availability |
| `pollinator_presence` | `str` | categorical | `scarce`, `moderate`, `abundant` | Critical bioindicator for reproductive ecosystem services |
| `invasive_species_pressure`| `str` | categorical | `none`, `low`, `moderate`, `severe` | Displacement pressure on indigenous biodiversity |

### 3.4 Climate & Weather Regime Layer (`ClimateProfile`)
| Variable | Type | Canonical Unit | Valid Range | Ecological Significance |
|---|---|---|---|---|
| `rainfall_mm` | `float` | `mm / year` | `0.0 - 10000.0` | `<400 mm` (semi-arid/arid water stress), `400-1000 mm` (sub-humid) |
| `temperature_mean_c`| `float` | `°C` | `-50.0 - 60.0` | Mean ambient thermal regime |
| `temperature_max_c` | `float` | `°C` | `-40.0 - 65.0` | Extreme thermal stress thresholds |
| `seasonality_pattern` | `str` | categorical | `unimodal`, `bimodal`, `erratic_drought`, `uniform` | Timing of moisture availability |
| `aridity_index` | `float` | P / PET | `0.0 - 5.0` | `<0.2` (arid), `0.2-0.5` (semi-arid), `0.5-0.65` (dry sub-humid) |

### 3.5 Human Impact & Pressures Layer (`HumanImpactProfile`)
| Variable | Type | Canonical Unit | Valid Range | Ecological Significance |
|---|---|---|---|---|
| `pollution_level` | `str` | categorical | `none`, `low`, `moderate`, `high`, `severe` | Chemical or heavy metal agrochemical stress |
| `pollution_type` | `list[str]`| list | `pesticides`, `synthetic_fertilizer`, `industrial_effluent`, `salinity` | Specific toxicological drivers |
| `deforestation_history` | `str` / `bool` | boolean / str | `recent (<5 yrs)`, `historic (>10 yrs)`, `none` | Legacy soil seed bank & mycorrhizal depletion |
| `habitat_fragmentation` | `str` | categorical | `continuous`, `moderate_fragmentation`, `severe_isolation` | Barrier to wildlife gene flow and seed dispersal |

### 3.6 Location & Spatial Metadata (`LocationProfile`)
| Variable | Type | Canonical Unit | Valid Range | Description |
|---|---|---|---|---|
| `region_name` | `str` | text | e.g. "Sahel", "Deccan Plateau", "Pampas", "Midwest US" | Biogeographic zone |
| `biome` | `str` | categorical | `semi_arid`, `tropical_dry_forest`, `temperate_grassland`, `boreal`, `mediterranean` | Global biome classification |
| `latitude` | `float` | decimal degrees | `-90.0 - 90.0` | Spatial coordinate |
| `longitude` | `float` | decimal degrees | `-180.0 - 180.0` | Spatial coordinate |
| `elevation_m` | `float` | meters ASL | `-500.0 - 9000.0` | Altitude above sea level |

---

## 4. Comprehensive Pydantic Schema Architecture

```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

class SoilProfile(BaseModel):
    ph: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="pH"))
    organic_carbon_percent: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="%"))
    moisture_percent: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="%"))
    bulk_density_g_cm3: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="g/cm3"))
    texture_class: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())

class LandProfile(BaseModel):
    land_use: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    land_cover: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    cropping_pattern: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    tillage_practice: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    canopy_cover_percent: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="%"))

class BiodiversityProfile(BaseModel):
    species_richness: EnvironmentalMetric[int] = Field(default_factory=lambda: EnvironmentalMetric[int](unit="count"))
    habitat_diversity: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    pollinator_presence: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    invasive_species_pressure: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())

class ClimateProfile(BaseModel):
    rainfall_mm_year: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="mm/year"))
    temperature_mean_c: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="°C"))
    temperature_max_c: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float](unit="°C"))
    seasonality_pattern: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    aridity_index: EnvironmentalMetric[float] = Field(default_factory=lambda: EnvironmentalMetric[float]())

class HumanImpactProfile(BaseModel):
    pollution_level: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    pollution_types: List[str] = Field(default_factory=list)
    deforestation: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())
    habitat_fragmentation: EnvironmentalMetric[str] = Field(default_factory=lambda: EnvironmentalMetric[str]())

class LocationProfile(BaseModel):
    region_name: Optional[str] = None
    biome: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    elevation_m: Optional[float] = None

class EnvironmentalProfile(BaseModel):
    profile_id: str
    created_at: str
    updated_at: str
    location: LocationProfile = Field(default_factory=LocationProfile)
    soil: SoilProfile = Field(default_factory=SoilProfile)
    land: LandProfile = Field(default_factory=LandProfile)
    biodiversity: BiodiversityProfile = Field(default_factory=BiodiversityProfile)
    climate: ClimateProfile = Field(default_factory=ClimateProfile)
    human_impact: HumanImpactProfile = Field(default_factory=HumanImpactProfile)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

---

## 5. Unit Normalization Pipeline

Raw inputs are normalized according to strict conversion rules:
- **Rainfall**: `inches/yr * 25.4 -> mm/yr`, `cm/yr * 10 -> mm/yr`
- **Temperature**: `(°F - 32) * 5/9 -> °C`, `K - 273.15 -> °C`
- **Soil Organic Matter (SOM) to SOC**: `SOC % ≈ SOM % / 1.724` (Van Bemmelen factor)
- **Soil Moisture**: Gravimetric (`g/g`) or volumetric (`cm³/cm³`) -> normalized percentage (`%`)

All normalization transformations are logged with the original input preserved in `metadata.raw_inputs`.

import pytest
from app.schemas.profile import (
    EnvironmentalProfile,
    ValueStatus,
    EnvironmentalMetric,
    SoilProfile,
    ClimateProfile,
    LandProfile
)

def test_environmental_metric_default_status():
    metric = EnvironmentalMetric[float]()
    assert metric.status == ValueStatus.MISSING
    assert metric.value is None
    assert not metric.is_known

def test_soil_profile_validations():
    # Valid pH
    soil = SoilProfile()
    soil.ph = EnvironmentalMetric[float](value=6.5, status=ValueStatus.PROVIDED)
    assert soil.ph.value == 6.5

    # Invalid pH (<0 or >14)
    with pytest.raises(ValueError, match="Soil pH 16.0 must be within range"):
        SoilProfile(ph=EnvironmentalMetric[float](value=16.0, status=ValueStatus.PROVIDED))

    # Invalid percentage (>100)
    with pytest.raises(ValueError, match="must be within range 0.0 to 100.0"):
        SoilProfile(organic_carbon_percent=EnvironmentalMetric[float](value=120.0, status=ValueStatus.PROVIDED))

def test_climate_rainfall_validation():
    with pytest.raises(ValueError, match="cannot be negative"):
        ClimateProfile(rainfall_mm_year=EnvironmentalMetric[float](value=-50.0, status=ValueStatus.PROVIDED))

def test_profile_merging():
    profile1 = EnvironmentalProfile()
    profile1.soil.organic_carbon_percent = EnvironmentalMetric[float](value=0.3, status=ValueStatus.PROVIDED)
    
    profile2 = EnvironmentalProfile()
    profile2.climate.rainfall_mm_year = EnvironmentalMetric[float](value=350.0, status=ValueStatus.PROVIDED)
    profile2.location.biome = "semi_arid"

    profile1.merge_with(profile2)

    assert profile1.soil.organic_carbon_percent.value == 0.3
    assert profile1.soil.organic_carbon_percent.status == ValueStatus.PROVIDED
    assert profile1.climate.rainfall_mm_year.value == 350.0
    assert profile1.location.biome == "semi_arid"

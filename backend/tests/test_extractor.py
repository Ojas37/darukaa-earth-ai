import pytest
from app.services.extractor import EnvironmentalExtractor
from app.schemas.profile import ValueStatus

@pytest.fixture
def extractor():
    return EnvironmentalExtractor()

def test_extract_full_scenario(extractor):
    text = "My farm is in a semi-arid region with very little rain. I grow only wheat and my soil carbon is around 0.3%."
    profile = extractor.extract(text)

    # Biome
    assert profile.location.biome == "semi_arid"
    
    # Soil Organic Carbon
    assert profile.soil.organic_carbon_percent.status == ValueStatus.PROVIDED
    assert profile.soil.organic_carbon_percent.value == 0.3

    # Land / Cropping
    assert profile.land.cropping_pattern.value == "monoculture"
    assert "wheat" in profile.land.primary_crops

    # Climate
    assert profile.climate.rainfall_pattern.value == "low_rainfall_semi_arid"
    assert profile.climate.rainfall_mm_year.is_known

def test_extract_unknown_values(extractor):
    text = "I don't know my soil carbon, but I get 400 mm rainfall and I practice monoculture corn."
    profile = extractor.extract(text)

    assert profile.soil.organic_carbon_percent.status == ValueStatus.UNKNOWN
    assert profile.climate.rainfall_mm_year.value == 400.0
    assert profile.climate.rainfall_mm_year.status == ValueStatus.PROVIDED
    assert profile.land.cropping_pattern.value == "monoculture"
    assert "corn" in profile.land.primary_crops

def test_extract_soil_ph_and_texture(extractor):
    text = "Our field is sandy loam with pH 7.2 receiving 500 mm rain."
    profile = extractor.extract(text)

    assert profile.soil.texture_class.value == "sandy loam"
    assert profile.soil.ph.value == 7.2
    assert profile.climate.rainfall_mm_year.value == 500.0

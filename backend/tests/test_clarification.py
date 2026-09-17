import pytest
from app.services.clarification import ClarificationEngine
from app.schemas.profile import EnvironmentalProfile, ValueStatus, EnvironmentalMetric

@pytest.fixture
def engine():
    return ClarificationEngine()

def test_clarification_needed_for_empty_profile(engine):
    profile = EnvironmentalProfile()
    needs_clarification, missing_items, prompt = engine.evaluate(profile)

    assert needs_clarification is True
    assert len(missing_items) <= 3
    assert any(item.category == "soil" for item in missing_items)
    assert any(item.category == "climate" for item in missing_items)
    assert any(item.category == "land" for item in missing_items)
    assert prompt is not None
    assert "Soil" in prompt
    assert "Climate" in prompt

def test_no_clarification_when_critical_info_provided(engine):
    profile = EnvironmentalProfile()
    profile.soil.organic_carbon_percent = EnvironmentalMetric[float](value=0.3, status=ValueStatus.PROVIDED)
    profile.climate.rainfall_mm_year = EnvironmentalMetric[float](value=350.0, status=ValueStatus.PROVIDED)
    profile.land.cropping_pattern = EnvironmentalMetric[str](value="monoculture", status=ValueStatus.PROVIDED)

    needs_clarification, missing_items, prompt = engine.evaluate(profile)

    assert needs_clarification is False
    assert len(missing_items) == 0
    assert prompt is None

def test_clarification_respects_unknown_status(engine):
    profile = EnvironmentalProfile()
    # User explicitly stated they don't know carbon
    profile.soil.organic_carbon_percent = EnvironmentalMetric[float](status=ValueStatus.UNKNOWN)
    profile.climate.rainfall_mm_year = EnvironmentalMetric[float](value=350.0, status=ValueStatus.PROVIDED)
    profile.land.cropping_pattern = EnvironmentalMetric[str](value="monoculture", status=ValueStatus.PROVIDED)

    needs_clarification, missing_items, prompt = engine.evaluate(profile)

    # Since soil is acknowledged as unknown, we don't block clarification
    assert needs_clarification is False

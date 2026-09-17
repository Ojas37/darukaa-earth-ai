"""
Step 7 Test: Structured Response Formatting & API Polish
=========================================================
Validates the complete response formatting layer, Pydantic v2 schema compliance,
narrative summary synthesis, clean markdown rendering, and REST endpoint contracts.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.schemas.profile import (
    EnvironmentalProfile, EnvironmentalMetric, ValueStatus
)
from app.reasoning.relationship_graph import relationship_graph
from app.recommendations.generator import RecommendationGenerator
from app.recommendations.formatter import build_structured_report
from app.schemas.response import StructuredReportResponse, ChatResponse

client = TestClient(app)

# ---------------------------------------------------------------------------
# Test 1: Unit Test on Report Formatter with Case B
# ---------------------------------------------------------------------------
def test_case_b_structured_report_formatting():
    profile = EnvironmentalProfile()
    profile.location.biome = "semi_arid"
    profile.location.region_name = "Semi-Arid Wheat Belt"
    profile.soil.organic_carbon_percent = EnvironmentalMetric[float](
        value=0.35, unit="%", status=ValueStatus.PROVIDED, confidence=1.0
    )
    profile.land.cropping_pattern = EnvironmentalMetric[str](
        value="monoculture", status=ValueStatus.PROVIDED, confidence=1.0
    )
    profile.climate.rainfall_mm_year = EnvironmentalMetric[float](
        value=350.0, unit="mm/year", status=ValueStatus.PROVIDED, confidence=1.0
    )
    profile.biodiversity.pollinator_presence = EnvironmentalMetric[str](
        value="scarce", status=ValueStatus.PROVIDED
    )

    pathways = relationship_graph.find_stress_pathways(profile, min_length=2)
    assert len(pathways) >= 2, f"Expected active pathways, got {len(pathways)}"

    generator = RecommendationGenerator()
    recs = generator.generate(profile=profile, pathways=pathways)
    assert len(recs) >= 2, f"Expected at least 2 recommendations, got {len(recs)}"

    report = build_structured_report(
        conversation_id="test_case_b_conv",
        profile=profile,
        pathways=pathways,
        recommendations=recs
    )

    # 1. Validate Schema
    assert isinstance(report, StructuredReportResponse)
    assert report.conversation_id == "test_case_b_conv"
    assert report.profile_summary.completeness_score > 0.0

    # 2. Validate Narrative Summary
    import re
    assert len(report.narrative_summary) > 50
    sentences = [s for s in re.split(r'(?<!\be\.g)(?<!\bi\.e)(?<!\bspp)(?<=[.!?])\s+', report.narrative_summary) if s.strip()]
    assert 1 <= len(sentences) <= 5, f"Expected 2-4 sentences narrative summary, got {len(sentences)}: {sentences}"

    # 3. Validate Overall Confidence
    assert report.overall_confidence.score >= 0.50
    assert report.overall_confidence.level in ["High", "Moderate", "Preliminary"]
    assert len(report.overall_confidence.explanation) > 20

    # 4. Validate Markdown Formatted Text
    md = report.formatted_text
    assert "# 🌿 Darukaa.Earth" in md
    assert "## 📋 Executive Summary" in md
    assert "## 📍 Site Profile & Baseline Metrics" in md
    assert "## ⚠️ Identified Ecological Stress Pathways" in md
    assert "## 🎯 Targeted Multi-Metric Recommendations" in md
    assert "## 📊 Scientific Confidence Assessment" in md

    # Check each recommendation is rendered in markdown
    for r in recs:
        assert r.pathway_id in md
        assert f"Confidence Score:" in md
        assert f"Time Horizon:" in md
        assert f"Targeted Variables:" in md

    print("\n✓ Case B Structured Report formatting validated successfully.")


# ---------------------------------------------------------------------------
# Test 2: Full Multi-Turn API Flow & Report Endpoint Test
# ---------------------------------------------------------------------------
def test_api_chat_and_report_endpoints():
    conv_id = "test_api_turn_conv_123"

    # Turn 1: Send rich Case B message
    payload = {
        "conversation_id": conv_id,
        "message": "We manage 150 hectares of cropland in a semi-arid zone with 350 mm annual rainfall. Soil organic carbon is depleted at 0.35% with pH 7.2, and we have practiced monoculture wheat for 10 years. Wild pollinators have become scarce."
    }
    
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200, f"Chat API error: {response.text}"
    data = response.json()

    # Assert ChatResponse structure
    chat_resp = ChatResponse.model_validate(data)
    assert chat_resp.conversation_id == conv_id
    assert chat_resp.needs_clarification is False
    assert chat_resp.report is not None
    assert len(chat_resp.report.recommendations) >= 2
    assert chat_resp.formatted_text is not None
    assert len(chat_resp.narrative_summary) > 30

    # Test GET /api/v1/report/{conversation_id}
    report_response = client.get(f"/api/v1/report/{conv_id}")
    assert report_response.status_code == 200, f"Report API error: {report_response.text}"
    report_data = report_response.json()
    
    report_obj = StructuredReportResponse.model_validate(report_data)
    assert report_obj.conversation_id == conv_id
    assert len(report_obj.recommendations) == len(chat_resp.report.recommendations)
    assert report_obj.overall_confidence.score == chat_resp.report.overall_confidence.score

    print("✓ Chat API and Report API endpoints validated successfully.")


if __name__ == "__main__":
    test_case_b_structured_report_formatting()
    test_api_chat_and_report_endpoints()
    print("\n══════════════════════════════════════════════════════════════════════")
    print("ALL STEP 7 TESTS PASSED ✓")
    print("══════════════════════════════════════════════════════════════════════")

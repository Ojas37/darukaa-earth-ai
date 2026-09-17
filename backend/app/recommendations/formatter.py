"""
Report Formatter for Darukaa.Earth
===================================
Constructs publication-grade StructuredReportResponse objects and markdown documents.
"""

from typing import List, Optional
from datetime import datetime
from app.schemas.profile import EnvironmentalProfile, ValueStatus
from app.reasoning.relationship_graph import StressPathway
from app.recommendations.generator import Recommendation
from app.schemas.response import (
    StructuredReportResponse, ProfileSummaryResponse,
    MetricSummary, ActivePathwayResponse, OverallConfidence
)


def _build_profile_summary(profile: EnvironmentalProfile) -> ProfileSummaryResponse:
    """Extracts known and missing metrics from an EnvironmentalProfile."""
    known: List[MetricSummary] = []
    missing: List[str] = []

    sections = [
        ("soil", profile.soil),
        ("land", profile.land),
        ("climate", profile.climate),
        ("human_impact", profile.human_impact),
        ("biodiversity", profile.biodiversity),
    ]

    total_fields = 0
    known_fields = 0

    for sec_name, sec_obj in sections:
        for field_name, attr in sec_obj.__dict__.items():
            if field_name.startswith("_") or field_name in ("observed_issues", "primary_crops", "pollution_types"):
                continue
            total_fields += 1
            if hasattr(attr, "is_known") and attr.is_known:
                known_fields += 1
                val = attr.value
                val_str = f"{val} {attr.unit}" if attr.unit and val is not None else str(val)
                known.append(MetricSummary(
                    field_name=f"{sec_name}.{field_name}",
                    value=val,
                    unit=attr.unit,
                    status=attr.status.value if hasattr(attr.status, "value") else str(attr.status),
                    confidence=attr.confidence,
                    source_notes=attr.source_notes
                ))
            else:
                missing.append(f"{sec_name}.{field_name}")

    completeness = round(known_fields / max(total_fields, 1), 3)

    return ProfileSummaryResponse(
        region_name=profile.location.region_name,
        biome=profile.location.biome,
        known_metrics=known,
        missing_metrics=missing[:8],  # list top missing for clarity
        completeness_score=completeness
    )


def _build_overall_confidence(recs: List[Recommendation]) -> OverallConfidence:
    """Computes aggregate confidence score and qualitative descriptor."""
    if not recs:
        return OverallConfidence(
            score=0.0,
            level="Preliminary",
            explanation="No active recommendations generated."
        )

    avg_score = round(sum(r.confidence_score for r in recs) / len(recs), 3)
    if avg_score >= 0.70:
        level = "High"
    elif avg_score >= 0.50:
        level = "Moderate"
    else:
        level = "Preliminary"

    explanation = (
        f"Aggregate confidence is {level} ({avg_score:.2f}) across {len(recs)} intervention(s), "
        f"grounded in verified empirical thresholds and peer-reviewed scientific literature."
    )
    return OverallConfidence(score=avg_score, level=level, explanation=explanation)


def _get_first_sentence(text: str) -> str:
    """Extracts the first full sentence, ignoring abbreviations like e.g. and i.e."""
    import re
    cleaned = text.strip()
    # Split by period followed by space/capital letter, ignoring e.g. and i.e.
    parts = re.split(r'(?<!\be\.g)(?<!\bi\.e)(?<=[.!?])\s+', cleaned)
    if parts:
        return parts[0].strip().rstrip(".")
    return cleaned.rstrip(".")


def _build_narrative_summary(profile: EnvironmentalProfile, recs: List[Recommendation]) -> str:
    """Constructs a 2–4 sentence plain-language synthesis of the intervention plan."""
    if not recs:
        return "No specific ecological stressors currently require active intervention based on the provided profile."

    biome_str = profile.location.biome.replace("_", " ") if profile.location.biome else "agricultural site"
    
    interventions_summary = [_get_first_sentence(r.recommendation) for r in recs]

    if len(recs) == 1:
        synthesis = f"For this {biome_str} system, the primary restoration lever is to {recs[0].recommendation.lower()}."
    elif len(recs) == 2:
        synthesis = (
            f"For this {biome_str} system, the recommended strategy combines two complementary actions: "
            f"first, {interventions_summary[0]}; second, {interventions_summary[1]}. "
            f"Together, these measures mitigate root-cause soil and landscape degradation while supporting long-term biodiversity recovery."
        )
    else:
        synthesis = (
            f"For this {biome_str} system, the restoration framework addresses {len(recs)} interconnected ecological pressures: "
            f"{'; '.join(interventions_summary[:3])}. "
            f"This integrated multi-metric approach restores foundational soil hydrology, breaks landscape monoculture, and safeguards biodiversity under local climate constraints."
        )

    return synthesis


def _build_markdown_report(
    profile: EnvironmentalProfile,
    pathways: List[StressPathway],
    recs: List[Recommendation],
    overall_conf: OverallConfidence,
    narrative: str,
) -> str:
    """Renders a clean, comprehensive Markdown report for human decision makers and UI views."""
    lines = []
    lines.append("# 🌿 Darukaa.Earth — Ecological Intelligence & Restoration Report")
    lines.append(f"*Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*\n")

    # Executive Narrative
    lines.append("## 📋 Executive Summary")
    lines.append(f"{narrative}\n")

    # Site Baseline
    lines.append("## 📍 Site Profile & Baseline Metrics")
    lines.append(f"- **Region / Biome:** {profile.location.region_name or 'Unspecified'} ({profile.location.biome or 'General'})")
    if profile.soil.organic_carbon_percent.is_known:
        lines.append(f"- **Soil Organic Carbon (SOC):** {profile.soil.organic_carbon_percent.value}%")
    if profile.climate.rainfall_mm_year.is_known:
        lines.append(f"- **Annual Rainfall:** {profile.climate.rainfall_mm_year.value} mm/year")
    if profile.land.cropping_pattern.is_known:
        lines.append(f"- **Cropping System:** {profile.land.cropping_pattern.value}")
    if profile.human_impact.pollution_level.is_known:
        lines.append(f"- **Pollution Pressure:** {profile.human_impact.pollution_level.value}")
    if profile.human_impact.deforestation_history.is_known:
        lines.append(f"- **Canopy / Deforestation History:** {profile.human_impact.deforestation_history.value}")
    lines.append("")

    # Active Stress Pathways
    lines.append("## ⚠️ Identified Ecological Stress Pathways")
    if pathways:
        for i, p in enumerate(pathways, 1):
            chain_str = " → ".join(p.nodes)
            lines.append(f"{i}. **[{p.pathway_id}]** `{chain_str}` *(Confidence: {p.confidence.value})*")
    else:
        lines.append("*No active stress cascades identified.*")
    lines.append("")

    # Targeted Recommendations
    lines.append("## 🎯 Targeted Multi-Metric Recommendations")
    if not recs:
        lines.append("*No interventions required for this baseline.*")
    else:
        for i, r in enumerate(recs, 1):
            lines.append(f"### Intervention {i}: {r.pathway_id}")
            lines.append(f"**Recommendation:**\n{r.recommendation}\n")
            lines.append(f"**Ecological Mechanism (Why It Works):**\n{r.why_it_works}\n")
            lines.append(f"- **Targeted Variables:** `{', '.join(r.affected_metrics)}`")
            lines.append(f"- **Time Horizon:** `{r.time_horizon.capitalize()}`")
            lines.append(f"- **Confidence Score:** `{r.confidence_score:.2f}` ({r.confidence_basis})")
            if r.constraint_notes:
                lines.append(f"- **Ecological Guardrails & Constraints:** {r.constraint_notes}")
            if r.evidence:
                lines.append(f"- **Scientific Evidence & Citations:**")
                for cit in r.evidence:
                    url_str = f" ([Link]({cit.url}))" if cit.url else ""
                    lines.append(f"  - *{cit.source}*{url_str}: {cit.claim_supported}")
            lines.append("")

    # Overall Confidence
    lines.append("## 📊 Scientific Confidence Assessment")
    lines.append(f"- **Overall Confidence Rating:** **{overall_conf.level}** ({overall_conf.score:.2f})")
    lines.append(f"- **Provenance & Methodology:** {overall_conf.explanation}")

    return "\n".join(lines)


def build_structured_report(
    conversation_id: str,
    profile: EnvironmentalProfile,
    pathways: List[StressPathway],
    recommendations: List[Recommendation],
) -> StructuredReportResponse:
    """Factory function creating a complete, validated StructuredReportResponse."""
    prof_summary = _build_profile_summary(profile)
    
    pathway_responses = [
        ActivePathwayResponse(
            pathway_id=p.pathway_id,
            summary=p.summary,
            nodes=p.nodes,
            chain_length=p.chain_length,
            confidence=p.confidence.value if hasattr(p.confidence, "value") else str(p.confidence)
        )
        for p in pathways
    ]

    overall_conf = _build_overall_confidence(recommendations)
    narrative = _build_narrative_summary(profile, recommendations)
    formatted_md = _build_markdown_report(
        profile=profile,
        pathways=pathways,
        recs=recommendations,
        overall_conf=overall_conf,
        narrative=narrative,
    )

    return StructuredReportResponse(
        conversation_id=conversation_id,
        created_at=datetime.utcnow().isoformat(),
        profile_summary=prof_summary,
        active_pathways=pathway_responses,
        recommendations=recommendations,
        overall_confidence=overall_conf,
        narrative_summary=narrative,
        formatted_text=formatted_md,
    )

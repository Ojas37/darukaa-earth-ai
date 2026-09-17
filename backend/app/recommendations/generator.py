"""
Step 6 — Multi-Metric Reasoning & Recommendation Generation
============================================================
Synthesises one evidence-constrained intervention per active StressPathway,
validated by claim_validator before being returned.

Design rules enforced here:
  • ONE recommendation per pathway (not per edge) — every recommendation
    must visibly address 2+ connected variables from the pathway's node sequence.
  • LLM receives ONLY retrieved evidence for that pathway's edges as its
    permitted quantitative source — it is explicitly told not to invent numbers.
  • All numeric claims in the generated text are run through ClaimValidator
    before the recommendation is returned; failing recs are rewritten qualitatively.
  • Ecological constraint checks are applied BEFORE LLM generation to guard
    against water-intensive proposals in semi-arid / arid profiles.
  • confidence_score is computed deterministically from profile completeness,
    evidence quality (similarity scores), and whether any counterpoints were
    retrieved for the pathway.
  • LLM provider: Anthropic Claude (if ANTHROPIC_API_KEY set) or Groq
    (if GROQ_API_KEY set, uses llama-3.3-70b-versatile). Anthropic takes
    precedence if both are present.
"""

import json
import logging
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.profile import EnvironmentalProfile
from app.reasoning.relationship_graph import StressPathway, EdgeStrength
from app.rag.retrieval import evidence_retriever
from app.rag.validation import claim_validator
from app.config import settings

# Groq model to use when ANTHROPIC_API_KEY is absent
GROQ_MODEL = "openai/gpt-oss-120b"

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output Schema
# ---------------------------------------------------------------------------

class EvidenceCitation(BaseModel):
    """Maps each quantitative claim in the recommendation text to a corpus entry."""
    source: str
    url: Optional[str] = None
    claim_supported: str = Field(
        ...,
        description="The exact quantitative claim from the recommendation that this entry supports."
    )


class Recommendation(BaseModel):
    """A single evidence-grounded, multi-metric intervention recommendation."""
    recommendation: str = Field(
        ...,
        description="Specific, actionable intervention. Not generic—tied to the profile's context."
    )
    why_it_works: str = Field(
        ...,
        description="Plain-language causal mechanism, directly connected to the pathway's edge chain."
    )
    affected_metrics: list[str] = Field(
        ...,
        min_length=2,
        description="EnvironmentalProfile node paths this intervention is projected to improve."
    )
    time_horizon: str = Field(
        ...,
        description="'short' (0–2 yr) | 'medium' (2–5 yr) | 'long' (5+ yr)"
    )
    evidence: list[EvidenceCitation] = Field(
        default_factory=list,
        description="Every quantitative figure must map to one of these corpus entries."
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Deterministic 0–1 score: profile completeness × evidence quality, tempered by counterpoints."
    )
    confidence_basis: str = Field(
        ...,
        description="Explains what the confidence_score is based on."
    )
    constraint_notes: Optional[str] = Field(
        default=None,
        description="Flags ecological contraindications (e.g. water-intensive in semi-arid) and how they were handled."
    )
    pathway_id: str = Field(
        ...,
        description="ID of the StressPathway this recommendation addresses."
    )
    validation_warnings: list[str] = Field(
        default_factory=list,
        description="Anti-hallucination warnings from claim validator."
    )


# ---------------------------------------------------------------------------
# Ecological Constraint Rules
# ---------------------------------------------------------------------------

# Each entry: (constraint_id, description, check_fn returning True if constraint FIRES)
_WATER_INTENSIVE_BIOMES = {"semi_arid", "arid"}
_LOW_RAINFALL_THRESHOLD_MM = 450.0


def _is_low_water_environment(profile: EnvironmentalProfile) -> bool:
    """Returns True if the profile indicates a water-scarce environment."""
    if profile.location.biome in _WATER_INTENSIVE_BIOMES:
        return True
    if (
        profile.climate.rainfall_mm_year.is_known
        and profile.climate.rainfall_mm_year.value is not None
        and profile.climate.rainfall_mm_year.value < _LOW_RAINFALL_THRESHOLD_MM
    ):
        return True
    if profile.climate.rainfall_pattern.is_known and "low" in str(
        profile.climate.rainfall_pattern.value
    ).lower():
        return True
    return False


CONSTRAINT_RULES = [
    {
        "id": "no_water_intensive_in_arid",
        "fires": _is_low_water_environment,
        "instruction": (
            "IMPORTANT ECOLOGICAL CONSTRAINT: This site is semi-arid or water-scarce "
            "(rainfall <450 mm/yr). Do NOT recommend irrigation-dependent species, "
            "water-intensive cover crops (e.g. Napier grass, water hyacinth), or "
            "practices requiring substantial supplemental water. Recommend drought-tolerant "
            "species only (e.g. Sorghum-Sudan hybrids, Cenchrus ciliaris, Stylosanthes, "
            "Sesbania sesban, or native perennial grasses). If a water-efficient alternative "
            "exists, prefer it. Document this constraint in constraint_notes."
        ),
        "note": (
            "Semi-arid / water-scarce site: water-intensive species excluded. "
            "Recommendation adapted to drought-tolerant alternatives."
        ),
    },
    {
        "id": "no_heavy_tillage_low_soc",
        "fires": lambda p: (
            p.soil.organic_carbon_percent.is_known
            and p.soil.organic_carbon_percent.value is not None
            and p.soil.organic_carbon_percent.value < 0.8
        ),
        "instruction": (
            "SOIL HEALTH CONSTRAINT: Soil organic carbon is critically low (<0.8%). "
            "Do NOT recommend deep inversion tillage or aggressive soil disturbance — "
            "these would further destroy fragile soil aggregates. Prefer no-till or "
            "minimum-till approaches."
        ),
        "note": (
            "Critically low SOC: heavy tillage excluded. No-till / minimum-till approach required."
        ),
    },
]


def _build_constraint_instructions(profile: EnvironmentalProfile) -> tuple[list[str], list[str]]:
    """Returns (list of LLM instruction strings, list of constraint note strings) for active constraints."""
    instructions = []
    notes = []
    for rule in CONSTRAINT_RULES:
        try:
            if rule["fires"](profile):
                instructions.append(rule["instruction"])
                notes.append(rule["note"])
        except Exception:
            pass
    return instructions, notes


# ---------------------------------------------------------------------------
# Confidence Scoring
# ---------------------------------------------------------------------------

def _compute_confidence(
    pathway: StressPathway,
    profile: EnvironmentalProfile,
    retrieved_evidence: list[dict],
) -> tuple[float, str]:
    """
    Deterministic confidence scorer.

    Components:
      • profile_completeness (0–0.4): proportion of pathway nodes that have known profile values
      • evidence_quality (0–0.4): mean similarity score of retrieved entries, floor-adjusted
      • evidence_directness (0–0.2): bonus if any retrieved entry targets this pathway's edges directly
      minus counterpoint_penalty (−0.1 per counterpoint, max −0.2)
    """
    basis_parts = []

    # 1. Profile completeness for this pathway's nodes
    node_fields = pathway.nodes  # e.g. ["soil.organic_carbon_percent", "soil.water_infiltration", ...]
    known_count = 0
    for node_path in node_fields:
        parts = node_path.split(".")
        if len(parts) == 2:
            section, field = parts
            try:
                section_obj = getattr(profile, section, None)
                if section_obj is not None:
                    metric = getattr(section_obj, field, None)
                    if metric is not None and hasattr(metric, "is_known") and metric.is_known:
                        known_count += 1
            except Exception:
                pass
    # Intermediate / derived nodes (like soil.water_infiltration, soil.moisture_stress)
    # aren't direct profile fields — only count the ones that actually resolve
    total_nodes = max(len(node_fields), 1)
    completeness_ratio = known_count / total_nodes
    profile_score = round(completeness_ratio * 0.4, 3)
    basis_parts.append(
        f"profile completeness {known_count}/{total_nodes} pathway nodes known → {profile_score:.2f}"
    )

    # 2. Evidence quality: mean similarity score of retrieved entries
    sim_scores = [e.get("similarity_score", 0.0) for e in retrieved_evidence]
    mean_sim = sum(sim_scores) / len(sim_scores) if sim_scores else 0.0
    evidence_quality_score = round(mean_sim * 0.4, 3)
    basis_parts.append(
        f"evidence quality mean_similarity={mean_sim:.3f} → {evidence_quality_score:.2f}"
    )

    # 3. Evidence directness: does any entry directly target this pathway's edges?
    pathway_edge_ids = {e.id for e in pathway.edges}
    direct_hits = sum(
        1 for ev in retrieved_evidence
        if any(eid in pathway_edge_ids for eid in ev.get("edge_ids", []))
    )
    directness_score = min(0.2, direct_hits * 0.1)
    basis_parts.append(
        f"{direct_hits} direct-edge evidence hit(s) → {directness_score:.2f}"
    )

    # 4. Counterpoint penalty
    counterpoints = [ev for ev in retrieved_evidence if ev.get("is_counterpoint", False)]
    penalty = min(0.2, len(counterpoints) * 0.1)
    if counterpoints:
        basis_parts.append(
            f"{len(counterpoints)} counterpoint(s) detected → −{penalty:.2f} penalty"
        )

    # 5. Pathway strength modifier
    strength_mod = {
        EdgeStrength.ESTABLISHED: 0.0,
        EdgeStrength.LIKELY: -0.05,
        EdgeStrength.CONTEXT_DEPENDENT: -0.1,
    }.get(pathway.confidence, 0.0)
    if strength_mod < 0:
        basis_parts.append(f"pathway confidence={pathway.confidence.value} → {strength_mod:.2f}")

    raw = profile_score + evidence_quality_score + directness_score - penalty + strength_mod
    final = round(max(0.0, min(1.0, raw)), 3)
    basis_parts.append(f"final={final}")

    return final, "; ".join(basis_parts)


# ---------------------------------------------------------------------------
# Prompt Construction
# ---------------------------------------------------------------------------

def _build_evidence_block(retrieved_evidence: list[dict]) -> str:
    """Formats retrieved corpus entries for LLM injection."""
    lines = []
    for i, ev in enumerate(retrieved_evidence, 1):
        caveat = ev.get("caveat") or ""
        caveat_str = f"\n   CAVEAT: {caveat}" if caveat else ""
        lines.append(
            f"[EV-{i}] ID={ev.get('id')} | Source: {ev.get('source')}\n"
            f"   Summary: {ev.get('summary')}{caveat_str}"
        )
    return "\n\n".join(lines) if lines else "No direct evidence retrieved for this pathway."


def _build_generation_prompt(
    profile: EnvironmentalProfile,
    pathway: StressPathway,
    retrieved_evidence: list[dict],
    constraint_instructions: list[str],
) -> str:
    profile_summary = json.dumps(profile.to_summary_dict(), indent=2)
    pathway_chain = " → ".join(pathway.nodes)
    evidence_block = _build_evidence_block(retrieved_evidence)
    constraint_block = "\n".join(constraint_instructions) if constraint_instructions else ""

    return f"""You are an AI environmental scientist for Darukaa.Earth.
Your task is to generate ONE specific, evidence-backed intervention recommendation
that addresses the ENTIRE causal stress pathway described below — not just a single node.

━━━━━━━━━━━━━━ SITE PROFILE ━━━━━━━━━━━━━━
{profile_summary}

━━━━━━━━━━━━━━ ACTIVE STRESS PATHWAY ━━━━━━━━━━━━━━
Pathway ID: {pathway.pathway_id}
Causal chain: {pathway_chain}
Pathway confidence: {pathway.confidence.value}

Edge mechanisms (in sequence):
{chr(10).join(f"  • {e.id}: {e.mechanism}" for e in pathway.edges)}

━━━━━━━━━━━━━━ PERMITTED EVIDENCE SOURCES ━━━━━━━━━━━━━━
You may ONLY cite the following peer-reviewed evidence entries.
Do NOT introduce any quantitative figure (percentage, measurement, count, fold-change)
that does not appear verbatim or in direct paraphrase in one of these entries.
If the evidence does not support a specific number, describe effects qualitatively.

{evidence_block}

{"━━━━━━━━━━━━━━ ACTIVE CONSTRAINTS ━━━━━━━━━━━━━━" + chr(10) + constraint_block if constraint_block else ""}

━━━━━━━━━━━━━━ OUTPUT FORMAT ━━━━━━━━━━━━━━
Return ONLY valid JSON (no markdown fences) matching this exact schema:
{{
  "recommendation": "<Specific, actionable intervention — 1–3 sentences. Must address ≥2 variables in the pathway chain. No generic phrases like 'use sustainable practices'.>",
  "why_it_works": "<Plain-language mechanistic explanation tied to the edge chain. 2–4 sentences.>",
  "affected_metrics": ["<node path from pathway>", ...],
  "time_horizon": "short" | "medium" | "long",
  "evidence": [
    {{
      "source": "<author/journal>",
      "url": "<url if available>",
      "claim_supported": "<exact quantitative figure from your recommendation text that this entry supports>"
    }}
  ],
  "constraint_notes": "<null or brief note if a water-intensive or ecologically incompatible option was excluded>"
}}

Rules:
- affected_metrics must contain at least 2 node paths from the pathway chain above.
- time_horizon: "short" = 0–2 years, "medium" = 2–5 years, "long" = 5+ years.
- evidence array may be empty if you made no quantitative claims.
- Do NOT include confidence_score or validation_warnings — those are computed separately.
- Output raw JSON only. No explanatory text."""


# ---------------------------------------------------------------------------
# Main Generator
# ---------------------------------------------------------------------------

class RecommendationGenerator:
    """
    Generates one evidence-constrained Recommendation per active StressPathway.

    Workflow per pathway:
      1. Retrieve per-edge evidence (already guaranteed ≥0.50 similarity floor).
      2. Build ecological constraint instructions from profile.
      3. Compute confidence_score deterministically.
      4. Call LLM (Anthropic or Groq) with evidence-locked prompt.
      5. Parse and validate — run ClaimValidator on generated text.
      6. Return finalised Recommendation or None if generation failed.
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
    ):
        self._provider: Optional[str] = None
        self.client = None

        # Anthropic takes precedence
        ant_key = anthropic_api_key or settings.anthropic_api_key
        groq_key = groq_api_key or getattr(settings, "groq_api_key", "")

        if ant_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=ant_key)
                self._provider = "anthropic"
                logger.info("RecommendationGenerator using Anthropic Claude.")
            except Exception as e:
                logger.warning(f"Failed to initialise Anthropic client: {e}")

        if self.client is None and groq_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=groq_key)
                self._provider = "groq"
                logger.info("RecommendationGenerator using Groq (llama-3.3-70b-versatile).")
            except ImportError:
                logger.warning("groq package not installed. Run: pip install groq")
            except Exception as e:
                logger.warning(f"Failed to initialise Groq client: {e}")

        if self.client is None:
            logger.warning(
                "No LLM client available. Set ANTHROPIC_API_KEY or GROQ_API_KEY in .env"
            )

    def _call_llm(self, prompt: str) -> str:
        """Provider-agnostic single-turn LLM call. Returns raw text response."""
        if self._provider == "anthropic":
            import anthropic
            response = self.client.messages.create(
                model=settings.anthropic_model,
                max_tokens=900,
                temperature=0.15,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()

        elif self._provider == "groq":
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                max_tokens=1500,
                temperature=0.15,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content.strip()

        raise RuntimeError("No LLM provider configured.")

    def generate(
        self,
        profile: EnvironmentalProfile,
        pathways: list[StressPathway],
        top_k_evidence_per_edge: int = 3,
    ) -> list[Recommendation]:
        """
        Generates one Recommendation per pathway.
        Returns a deduplicated list of validated Recommendation objects.
        """
        if self.client is None:
            logger.warning("No LLM client — skipping recommendation generation.")
            return []

        recommendations: list[Recommendation] = []
        # Track which pathway start→terminal pairs we've already covered to avoid near-duplicate recs
        covered_pairs: set[tuple[str, str]] = set()

        constraint_instructions, constraint_notes_list = _build_constraint_instructions(profile)

        for pathway in pathways:
            pair = (pathway.start_variable, pathway.terminal_variable)
            if pair in covered_pairs:
                logger.debug(f"Skipping duplicate pathway pair {pair}")
                continue
            covered_pairs.add(pair)

            rec = self._generate_for_pathway(
                profile=profile,
                pathway=pathway,
                constraint_instructions=constraint_instructions,
                constraint_notes_list=constraint_notes_list,
                top_k_evidence_per_edge=top_k_evidence_per_edge,
            )
            if rec is not None:
                recommendations.append(rec)

        return recommendations

    def _generate_for_pathway(
        self,
        profile: EnvironmentalProfile,
        pathway: StressPathway,
        constraint_instructions: list[str],
        constraint_notes_list: list[str],
        top_k_evidence_per_edge: int,
    ) -> Optional[Recommendation]:
        """Generates and validates one recommendation for a single pathway."""

        # 1. Retrieve evidence covering this pathway's edges
        active_edge_ids = [e.id for e in pathway.edges]
        query = (
            f"biodiversity restoration intervention "
            f"{profile.location.biome or 'cropland'} "
            f"{' '.join(e.source_node.split('.')[-1] for e in pathway.edges)}"
        )
        retrieved_evidence = evidence_retriever.retrieve(
            query=query,
            biome=profile.location.biome,
            climate_zone=(
                str(profile.climate.rainfall_pattern.value)
                if profile.climate.rainfall_pattern.is_known else None
            ),
            edge_ids=active_edge_ids,
            top_k=top_k_evidence_per_edge,
        )

        # 2. Deterministic confidence score
        confidence_score, confidence_basis = _compute_confidence(pathway, profile, retrieved_evidence)

        # 3. Build prompt and call LLM
        prompt = _build_generation_prompt(
            profile=profile,
            pathway=pathway,
            retrieved_evidence=retrieved_evidence,
            constraint_instructions=constraint_instructions,
        )

        try:
            raw_text = self._call_llm(prompt)
        except Exception as e:
            logger.error(f"LLM call failed for {pathway.pathway_id}: {e}")
            return None

        # 4. Parse JSON
        try:
            cleaned = raw_text
            for fence in ("```json", "```"):
                if cleaned.startswith(fence):
                    cleaned = cleaned[len(fence):]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error for {pathway.pathway_id}: {e}\nRaw:\n{raw_text[:300]}")
            return None

        # 5. Validate & possibly rewrite quantitative claims
        rec_text = data.get("recommendation", "") + " " + data.get("why_it_works", "")
        validation_result = claim_validator.validate_claim(rec_text, retrieved_evidence)

        if not validation_result.is_valid:
            # Rewrite the recommendation with qualitative language
            logger.info(
                f"Claim validation rewrote {pathway.pathway_id}: "
                f"unsupported={validation_result.unsupported_numbers}"
            )
            rewritten_text = validation_result.rewritten_claim or rec_text
            # Attempt to split rewritten back into recommendation / why_it_works
            # (best-effort split at sentence boundary)
            sentences = [s.strip() for s in rewritten_text.split(".") if s.strip()]
            mid = max(1, len(sentences) // 2)
            data["recommendation"] = ". ".join(sentences[:mid]) + "."
            data["why_it_works"] = ". ".join(sentences[mid:]) + "." if sentences[mid:] else data.get("why_it_works", "")

        # 6. Build evidence citations from retrieved entries
        evidence_citations: list[EvidenceCitation] = []
        for ev_dict in data.get("evidence", []):
            try:
                evidence_citations.append(EvidenceCitation(**ev_dict))
            except Exception:
                pass

        # Fall back: if LLM returned no citations but we have retrieved evidence, attach top entries
        if not evidence_citations and retrieved_evidence:
            for ev in retrieved_evidence[:2]:
                evidence_citations.append(EvidenceCitation(
                    source=ev.get("source", ""),
                    url=ev.get("url"),
                    claim_supported="Supporting evidence for this pathway's causal mechanism.",
                ))

        # 7. Build affected_metrics — merge LLM output with pathway nodes as ground truth
        llm_metrics = data.get("affected_metrics", [])
        pathway_nodes = pathway.nodes
        # Ensure at least the pathway's first and last nodes are present
        combined_metrics = list(dict.fromkeys(
            llm_metrics + [pathway_nodes[0], pathway_nodes[-1]]
        ))[:6]  # cap at 6 for clarity

        # 8. Constraint notes
        constraint_note = data.get("constraint_notes") or None
        if constraint_notes_list and not constraint_note:
            constraint_note = "; ".join(constraint_notes_list)

        # 9. Validate time_horizon field
        valid_horizons = {"short", "medium", "long"}
        time_horizon = data.get("time_horizon", "medium")
        if time_horizon not in valid_horizons:
            time_horizon = "medium"

        return Recommendation(
            recommendation=data.get("recommendation", "").strip(),
            why_it_works=data.get("why_it_works", "").strip(),
            affected_metrics=combined_metrics,
            time_horizon=time_horizon,
            evidence=evidence_citations,
            confidence_score=confidence_score,
            confidence_basis=confidence_basis,
            constraint_notes=constraint_note,
            pathway_id=pathway.pathway_id,
            validation_warnings=validation_result.warnings,
        )


# Module-level singleton
recommendation_generator = RecommendationGenerator()

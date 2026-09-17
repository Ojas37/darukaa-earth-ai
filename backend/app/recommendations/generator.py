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

# Source-type credibility keywords
_META_ANALYSIS_KEYWORDS = ["meta-analysis", "meta analysis", "systematic review", "1,705", "157 studies", "89 field", "global synthesis"]
_INSTITUTIONAL_KEYWORDS = ["ipcc", "fao", "ipbes", "special report", "assessment report"]
_MULTI_SITE_KEYWORDS = ["multi-site", "global survey", "landscape scale", "across regions"]


def _get_source_weight(source_str: str, summary_str: str = "") -> float:
    """Returns credibility weight based on study design."""
    combined = f"{source_str} {summary_str}".lower()
    if any(k in combined for k in _META_ANALYSIS_KEYWORDS):
        return 1.0
    if any(k in combined for k in _INSTITUTIONAL_KEYWORDS):
        return 0.85
    if any(k in combined for k in _MULTI_SITE_KEYWORDS):
        return 0.75
    return 0.60  # single-site / local empirical study


def _compute_confidence(
    pathway: StressPathway,
    profile: EnvironmentalProfile,
    retrieved_evidence: list[dict],
) -> tuple[float, str]:
    """
    Deterministic confidence scorer.

    Components:
      • profile_grounding (0–0.40):
          - Root trigger variable is provided with high confidence in profile: +0.25
          - Terminal impact variable / observation is corroborated in profile: +0.15
      • evidence_quality (0–0.40):
          - Mean of (similarity_score × source_weight) normalized to 0–0.40
      • evidence_directness (0–0.20):
          - Direct edge coverage bonus (0.07 per direct hit, max 0.20)
      • counterpoint_penalty (−0.10 per counterpoint, max −0.20)
      • pathway_strength_mod (0.0 for ESTABLISHED, -0.05 for LIKELY, -0.10 for CONTEXT_DEPENDENT)
    """
    basis_parts = []

    # 1. Profile grounding: check if the root trigger and terminal impact are anchored in profile
    root_node = pathway.start_variable
    term_node = pathway.terminal_variable
    
    root_grounded = False
    root_parts = root_node.split(".")
    if len(root_parts) == 2:
        sec, fld = root_parts
        sec_obj = getattr(profile, sec, None)
        if sec_obj:
            metric = getattr(sec_obj, fld, None)
            if metric and hasattr(metric, "is_known") and metric.is_known:
                root_grounded = True
    
    # Terminal grounding (check direct metric or related observed issues)
    term_grounded = False
    term_parts = term_node.split(".")
    if len(term_parts) == 2:
        sec, fld = term_parts
        sec_obj = getattr(profile, sec, None)
        if sec_obj:
            metric = getattr(sec_obj, fld, None)
            if metric and hasattr(metric, "is_known") and metric.is_known:
                term_grounded = True
    
    # Also check qualitative observations (e.g. pollinator decline in biodiversity)
    if "pollinator" in term_node and (
        profile.biodiversity.pollinator_presence.is_known
        or "pollinator_decline" in profile.biodiversity.observed_issues
    ):
        term_grounded = True
    elif "species_richness" in term_node and (
        profile.biodiversity.species_richness.is_known
        or "biodiversity_loss" in profile.biodiversity.observed_issues
    ):
        term_grounded = True

    profile_grounding_score = 0.0
    if root_grounded:
        profile_grounding_score += 0.25
    if term_grounded:
        profile_grounding_score += 0.15
    profile_grounding_score = round(profile_grounding_score, 3)

    basis_parts.append(
        f"profile grounding (root={root_grounded}, terminal={term_grounded}) → {profile_grounding_score:.2f}"
    )

    # 2. Evidence quality: weighted similarity by study type (meta-analysis > single study)
    if retrieved_evidence:
        weighted_sims = []
        for ev in retrieved_evidence:
            sim = ev.get("similarity_score", 0.70)
            src = ev.get("source", "")
            summ = ev.get("summary", "")
            wt = _get_source_weight(src, summ)
            weighted_sims.append(sim * wt)
        mean_weighted_sim = sum(weighted_sims) / len(weighted_sims)
    else:
        mean_weighted_sim = 0.0

    evidence_quality_score = round(min(0.40, mean_weighted_sim * 0.45), 3)
    basis_parts.append(
        f"evidence quality (weighted_sim={mean_weighted_sim:.3f}) → {evidence_quality_score:.2f}"
    )

    # 3. Evidence directness: how many pathway edges are directly targeted by corpus entries
    pathway_edge_ids = {e.id for e in pathway.edges}
    direct_hits = sum(
        1 for ev in retrieved_evidence
        if any(eid in pathway_edge_ids for eid in ev.get("edge_ids", []))
    )
    directness_score = round(min(0.20, direct_hits * 0.07), 3)
    basis_parts.append(
        f"{direct_hits} direct-edge hit(s) → {directness_score:.2f}"
    )

    # 4. Counterpoint penalty
    counterpoints = [
        ev for ev in retrieved_evidence
        if ev.get("is_counterpoint", False) or "guardrail" in str(ev.get("status", "")).lower()
    ]
    penalty = round(min(0.20, len(counterpoints) * 0.10), 3)
    if penalty > 0:
        basis_parts.append(
            f"{len(counterpoints)} counterpoint(s) detected → −{penalty:.2f} penalty"
        )

    # 5. Pathway strength modifier
    strength_mod = {
        EdgeStrength.ESTABLISHED: 0.0,
        EdgeStrength.LIKELY: -0.05,
        EdgeStrength.CONTEXT_DEPENDENT: -0.10,
    }.get(pathway.confidence, 0.0)
    if strength_mod < 0:
        basis_parts.append(f"pathway confidence={pathway.confidence.value} → {strength_mod:.2f}")

    raw = profile_grounding_score + evidence_quality_score + directness_score - penalty + strength_mod
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
            f"[EV-{i}] ID={ev.get('id')} | Source: {ev.get('source')} | URL: {ev.get('url')}\n"
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
      "evidence_id": "<ID of the cited entry, e.g. ev_001>",
      "claim_supported": "<exact quantitative figure or qualitative effect supported>"
    }}
  ],
  "constraint_notes": "<null or brief note if a water-intensive or ecologically incompatible option was excluded>"
}}

Rules:
- affected_metrics must contain at least 2 node paths from the pathway chain above.
- time_horizon: "short" = 0–2 years, "medium" = 2–5 years, "long" = 5+ years.
- In the evidence array, use the exact evidence_id (e.g. ev_001, ev_008) from the permitted sources above.
- Do NOT include confidence_score or validation_warnings — those are computed separately.
- Output raw JSON only. No explanatory text."""


# ---------------------------------------------------------------------------
# Deduplication Helpers
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were",
    "will", "with", "this", "such", "using", "into", "through", "across", "other"
}


def _normalize_unicode(text: str) -> str:
    """Normalizes non-breaking spaces, unicode dashes/hyphens, and quotes to ASCII."""
    if not text:
        return text
    text = text.replace("\u00a0", " ")
    for dash in ["\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"]:
        text = text.replace(dash, "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    return text


def _compute_text_jaccard(text1: str, text2: str) -> float:
    """Computes content-word Jaccard similarity between two texts."""
    import re
    w1 = set(re.findall(r"\b[a-zA-Z]{3,}\b", text1.lower())) - _STOPWORDS
    w2 = set(re.findall(r"\b[a-zA-Z]{3,}\b", text2.lower())) - _STOPWORDS
    if not w1 or not w2:
        return 0.0
    intersection = len(w1 & w2)
    union = len(w1 | w2)
    return intersection / union if union > 0 else 0.0


def _filter_subsumed_pathways(pathways: list[StressPathway]) -> list[StressPathway]:
    """
    Suppresses shorter sub-chains when a strictly more comprehensive causal chain
    sharing the same terminal variable is already present.
    """
    # Sort longest first so we prioritize maximal root-to-terminal chains
    sorted_paths = sorted(pathways, key=lambda p: len(p.nodes), reverse=True)
    selected: list[StressPathway] = []

    for path in sorted_paths:
        is_subsumed = False
        path_nodes_set = set(path.nodes)
        for existing in selected:
            # If the current pathway's nodes are a subset of an existing longer pathway
            # and they target the same terminal outcome, it's subsumed
            if (
                path.terminal_variable == existing.terminal_variable
                and path_nodes_set.issubset(set(existing.nodes))
            ):
                logger.debug(
                    f"Subsuming pathway {path.pathway_id} ({len(path.nodes)} nodes) into "
                    f"{existing.pathway_id} ({len(existing.nodes)} nodes)"
                )
                is_subsumed = True
                break
        if not is_subsumed:
            selected.append(path)

    return selected


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
      6. Deduplicate semantically and return finalized Recommendation objects.
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
                max_tokens=3000,
                temperature=0.15,
                response_format={"type": "json_object"},
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
        Generates one Recommendation per distinct pathway.
        Returns a deduplicated list of validated Recommendation objects.
        """
        if self.client is None:
            logger.warning("No LLM client — skipping recommendation generation.")
            return []

        # 1. Prune pathways that are sub-chains of longer active pathways
        pruned_pathways = _filter_subsumed_pathways(pathways)
        logger.info(f"Generating recommendations for {len(pruned_pathways)} non-subsumed pathways (from {len(pathways)} total).")

        constraint_instructions, constraint_notes_list = _build_constraint_instructions(profile)
        candidate_recs: list[Recommendation] = []

        for pathway in pruned_pathways:
            rec = self._generate_for_pathway(
                profile=profile,
                pathway=pathway,
                constraint_instructions=constraint_instructions,
                constraint_notes_list=constraint_notes_list,
                top_k_evidence_per_edge=top_k_evidence_per_edge,
            )
            if rec is not None:
                candidate_recs.append(rec)

        # 2. Semantic text deduplication pass
        terminal_map = {p.pathway_id: p.terminal_variable for p in pathways}

        final_recs: list[Recommendation] = []
        for cand in candidate_recs:
            is_dup = False
            cand_term = terminal_map.get(cand.pathway_id, "")
            for i, kept in enumerate(final_recs):
                kept_term = terminal_map.get(kept.pathway_id, "")
                sim = _compute_text_jaccard(cand.recommendation, kept.recommendation)
                
                # Same terminal outcome: merge if Jaccard >= 0.50
                # Different terminal outcome: only merge if near-verbatim duplicate (>= 0.65)
                threshold = 0.50 if (cand_term and cand_term == kept_term) else 0.65
                if sim >= threshold:
                    logger.info(f"Duplicate recommendation detected (sim={sim:.2f}, threshold={threshold}). Comparing confidence scores.")
                    if cand.confidence_score > kept.confidence_score:
                        final_recs[i] = cand
                    is_dup = True
                    break
            if not is_dup:
                final_recs.append(cand)

        return final_recs

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

        # 3. Build prompt and call LLM (with 1 retry on JSON error)
        prompt = _build_generation_prompt(
            profile=profile,
            pathway=pathway,
            retrieved_evidence=retrieved_evidence,
            constraint_instructions=constraint_instructions,
        )

        data = None
        for attempt in range(2):
            try:
                raw_text = self._call_llm(prompt)
                cleaned = raw_text
                for fence in ("```json", "```"):
                    if cleaned.startswith(fence):
                        cleaned = cleaned[len(fence):]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
                data = json.loads(cleaned)
                break
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} generation failed for {pathway.pathway_id}: {e}")
                if attempt == 1:
                    logger.error(f"Generation failed after retry for {pathway.pathway_id}")
                    return None

        if not data:
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

        # 6. Build evidence citations with hard provenance check
        raw_citations = data.get("evidence", [])
        verified_cits, cit_warnings = claim_validator.validate_citations(
            raw_citations, retrieved_evidence
        )

        # Fall back: if LLM returned no citations but we have retrieved evidence, attach top entries
        if not verified_cits and retrieved_evidence:
            for ev in retrieved_evidence[:2]:
                verified_cits.append({
                    "source": ev.get("source", ""),
                    "url": ev.get("url"),
                    "claim_supported": "Supporting evidence for this pathway's causal mechanism.",
                })

        evidence_citations: list[EvidenceCitation] = []
        for vc in verified_cits:
            try:
                evidence_citations.append(EvidenceCitation(
                    source=_normalize_unicode(vc.get("source", "")),
                    url=vc.get("url"),
                    claim_supported=_normalize_unicode(vc.get("claim_supported", ""))
                ))
            except Exception:
                pass

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

        all_warnings = list(dict.fromkeys(validation_result.warnings + cit_warnings))

        return Recommendation(
            recommendation=_normalize_unicode(data.get("recommendation", "").strip()),
            why_it_works=_normalize_unicode(data.get("why_it_works", "").strip()),
            affected_metrics=combined_metrics,
            time_horizon=time_horizon,
            evidence=evidence_citations,
            confidence_score=confidence_score,
            confidence_basis=confidence_basis,
            constraint_notes=_normalize_unicode(constraint_note) if constraint_note else None,
            pathway_id=pathway.pathway_id,
            validation_warnings=all_warnings,
        )


# Module-level singleton
recommendation_generator = RecommendationGenerator()

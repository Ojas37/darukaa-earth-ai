import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ValidationResult(BaseModel):
    is_valid: bool = Field(..., description="True if all quantitative claims are grounded in retrieved evidence")
    unsupported_numbers: List[str] = Field(default_factory=list, description="List of numeric figures present in claim but absent from evidence")
    supported_numbers: List[str] = Field(default_factory=list, description="List of verified grounded numeric figures")
    active_counterpoints: List[Dict[str, Any]] = Field(default_factory=list, description="Critical scientific caveats or tempering evidence detected")
    rewritten_claim: Optional[str] = Field(default=None, description="Conservative qualitative rewrite if ungrounded numbers were detected")
    warnings: List[str] = Field(default_factory=list, description="Scientifically informative warnings")

class ClaimValidator:
    """
    Anti-Hallucination & Scientific Grounding Verification Layer.
    Audits generated claims against retrieved scientific corpus entries to guarantee:
    1. Quantitative effect-size figures (percentages, rates, measurements) trace to peer-reviewed excerpts.
    2. Incidental numbers (time horizons, durations like '6 months', publication years, list steps) pass through untouched.
    3. Ungrounded effect figures are flagged and rewritten conservatively as qualitative guidance.
    4. Counterpoint / tempering evidence (e.g. ev_002) is highlighted rather than obscured.
    """

    # Regex for incidental numbers that should NOT be treated as effect claims
    DURATION_PATTERN = re.compile(
        r"\b(?:\d+(?:\.\d+)?|\d+\s*-\s*\d+)\s*(?:months?|weeks?|days?|years?|decades?|seasons?|hrs?|hours?)\b",
        re.IGNORECASE
    )
    YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
    LIST_STEP_PATTERN = re.compile(r"(?:^|\s)(?:step\s*\d+|\d+\.)(?:\s|$)", re.IGNORECASE)

    # Patterns indicating quantitative effect claims:
    # 1. Percentages (e.g. 59%, 35%, 48.5%)
    # 2. Measurements with units (e.g. 70mm, 2-5.6 degrees C, 1.5 t C/ha)
    # 3. Large statistical counts / sample sizes (e.g. 1,705, 50,000)
    # 4. Multipliers / fold-changes (e.g. 2-fold, 3x)
    PERCENT_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\s*%", re.IGNORECASE)
    MEASUREMENT_PATTERN = re.compile(
        r"\b\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?\s*(?:mm|millimeters|cm|°C|degrees\s*c|t\s*c/ha|g/cm3|fold|times)\b",
        re.IGNORECASE
    )
    LARGE_STAT_COUNT_PATTERN = re.compile(r"\b\d{1,3}(?:,\d{3})+\b")

    def validate_claim(self, claim_text: str, retrieved_entries: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validates a claim against retrieved scientific evidence entries.
        """
        extracted_claim_numbers = self._extract_effect_numbers(claim_text)
        evidence_corpus_text = " ".join([e.get("summary", "") for e in retrieved_entries])
        evidence_numbers = self._extract_effect_numbers(evidence_corpus_text)

        supported_numbers: List[str] = []
        unsupported_numbers: List[str] = []

        # Check each effect number in the claim
        for num in extracted_claim_numbers:
            if self._is_number_supported(num, evidence_corpus_text, evidence_numbers):
                supported_numbers.append(num)
            else:
                unsupported_numbers.append(num)

        # Check for active counterpoints in retrieved evidence
        active_counterpoints: List[Dict[str, Any]] = []
        for entry in retrieved_entries:
            if entry.get("is_counterpoint") or "counterpoint" in entry.get("topic", "").lower() or "guardrail" in str(entry.get("status", "")).lower():
                active_counterpoints.append({
                    "id": entry.get("id"),
                    "topic": entry.get("topic"),
                    "caveat": entry.get("caveat"),
                    "source": entry.get("source"),
                    "guidance": "Tempering Evidence: This study cautions against overstating direct single-variable effects. Present recommendations in terms of diversified practices rather than linear carbon/yield multipliers."
                })

        is_valid = len(unsupported_numbers) == 0
        rewritten_claim = None
        warnings = []

        if not is_valid:
            warnings.append(
                f"Anti-Hallucination Flag: The claim contains ungrounded quantitative figure(s): {', '.join(unsupported_numbers)}. Rewriting to qualitative guidance."
            )
            rewritten_claim = self._rewrite_qualitatively(claim_text, unsupported_numbers)

        if active_counterpoints:
            warnings.append(
                f"Tempering Nuance Active: {len(active_counterpoints)} evidence counterpoint(s) detected (e.g. {active_counterpoints[0]['id']})."
            )

        return ValidationResult(
            is_valid=is_valid,
            unsupported_numbers=unsupported_numbers,
            supported_numbers=supported_numbers,
            active_counterpoints=active_counterpoints,
            rewritten_claim=rewritten_claim or claim_text,
            warnings=warnings
        )

    def _extract_effect_numbers(self, text: str) -> List[str]:
        """
        Extracts quantitative effect figures (percentages, metrics, large counts, fold-changes)
        while explicitly excluding time horizons, durations (e.g. '6 months', '2-3 years'),
        publication years (e.g. '2019'), and list enumerations.
        """
        effect_numbers = set()

        # 1. Extract percentages (e.g. 59%, 35%, 45%)
        for m in self.PERCENT_PATTERN.finditer(text):
            effect_numbers.add(m.group(0).strip())

        # 2. Extract measurements with units (e.g. 70mm, 2-5.6 degrees C)
        for m in self.MEASUREMENT_PATTERN.finditer(text):
            effect_numbers.add(m.group(0).strip())

        # 3. Extract large counts / sample sizes (e.g. 1,705, 50,000)
        for m in self.LARGE_STAT_COUNT_PATTERN.finditer(text):
            effect_numbers.add(m.group(0).strip())

        # 4. Check for unattached naked numbers representing effect claims (e.g. "raised by 45")
        # Mask out durations, years, and list steps first
        masked_text = self.DURATION_PATTERN.sub(" [DURATION] ", text)
        masked_text = self.YEAR_PATTERN.sub(" [YEAR] ", masked_text)
        masked_text = self.LIST_STEP_PATTERN.sub(" [STEP] ", masked_text)

        # Find any remaining naked effect percentages/decimals in masked text
        for m in re.finditer(r"\b(?:\d+\.\d+|\d{2,})\b", masked_text):
            val = m.group(0).strip()
            # If not already captured and not a year
            if not any(val in en for en in effect_numbers):
                effect_numbers.add(val)

        return sorted(list(effect_numbers))

    def _is_number_supported(self, candidate_num: str, evidence_text: str, evidence_numbers: List[str]) -> bool:
        """
        Checks if candidate_num is directly present or mathematically encompassed in the evidence.
        """
        # Exact match in raw text or evidence numbers
        if candidate_num.lower() in evidence_text.lower():
            return True

        # Normalized match (strip % or commas or spaces)
        cand_clean = candidate_num.replace("%", "").replace(",", "").strip().lower()
        for ev_num in evidence_numbers:
            ev_clean = ev_num.replace("%", "").replace(",", "").strip().lower()
            if cand_clean == ev_clean:
                return True
            # Check range inclusion: e.g. "76" within "76-80" or "2" within "2-5.6"
            if "-" in ev_clean:
                parts = ev_clean.split("-")
                if len(parts) == 2 and cand_clean in [p.strip() for p in parts]:
                    return True

        return False

    def _rewrite_qualitatively(self, text: str, ungrounded_numbers: List[str]) -> str:
        """
        Converts ungrounded quantitative effect assertions into scientifically safe qualitative guidance,
        preserving durations (e.g. 'over 6 months') and non-effect text intact.
        """
        rewritten = text
        for num in ungrounded_numbers:
            pattern = rf"(?:\b(?:by|at|around|approx(?:imately)?)\s+)?{re.escape(num)}"
            rewritten = re.sub(pattern, "substantially", rewritten, flags=re.IGNORECASE)
            rewritten = re.sub(rf"\b{re.escape(num)}\b", "measurable", rewritten)

        rewritten = re.sub(r"\bsubstantially\s+substantially\b", "substantially", rewritten, flags=re.IGNORECASE)
        rewritten = re.sub(r"\s+", " ", rewritten).strip()
        return rewritten

    def validate_citations(
        self,
        citations: List[Dict[str, Any]],
        retrieved_entries: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Hard check for citation provenance:
        Asserts that every citation url matches a verified URL from the retrieved evidence entries.
        Replaces hallucinated or generated URLs with the exact corpus URL, or drops unverified citations.
        """
        warnings = []
        verified_citations = []

        retrieved_by_id = {e.get("id"): e for e in retrieved_entries if e.get("id")}
        retrieved_urls = {e.get("url") for e in retrieved_entries if e.get("url")}

        for cit in citations:
            source = cit.get("source", "")
            url = cit.get("url")
            claim_supported = cit.get("claim_supported", "")
            evidence_id = cit.get("evidence_id")

            matched_entry = None
            if evidence_id and evidence_id in retrieved_by_id:
                matched_entry = retrieved_by_id[evidence_id]
            else:
                for e in retrieved_entries:
                    e_src = e.get("source", "")
                    if e_src == source or (source and (source.lower() in e_src.lower() or e_src.lower() in source.lower())):
                        matched_entry = e
                        break
                    s_author = source.split(",")[0].split()[0].lower() if source else ""
                    e_author = e_src.split(",")[0].split()[0].lower() if e_src else ""
                    if s_author and len(s_author) > 3 and s_author == e_author:
                        matched_entry = e
                        break

            if matched_entry:
                correct_url = matched_entry.get("url")
                if url and url != correct_url:
                    warnings.append(
                        f"Citation URL provenance corrected for '{matched_entry.get('id')}': replaced unverified '{url}' with verified corpus URL '{correct_url}'."
                    )
                verified_citations.append({
                    "source": matched_entry.get("source", source),
                    "url": correct_url,
                    "claim_supported": claim_supported or "Supporting evidence for this pathway's causal mechanism."
                })
            else:
                if url and url in retrieved_urls:
                    verified_citations.append(cit)
                else:
                    warnings.append(
                        f"Unverified citation dropped: '{source}' ({url}) does not match any retrieved evidence entry."
                    )

        return verified_citations, warnings

claim_validator = ClaimValidator()

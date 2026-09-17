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
    1. Quantitative figures trace to peer-reviewed excerpts.
    2. Ungrounded figures are flagged and rewritten conservatively as qualitative guidance.
    3. Counterpoint / tempering evidence (e.g. ev_002) is highlighted rather than obscured.
    """

    # Numbers to ignore (years, standard list indices, etc.)
    IGNORED_NUMBER_PATTERNS = [
        r"^(?:19|20)\d{2}$",      # Publication years like 1999, 2019, 2026
        r"^[1-9]\.$",             # List indices like 1., 2., 3.
        r"^v\d+$"                 # Version numbers
    ]

    def validate_claim(self, claim_text: str, retrieved_entries: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validates a claim against retrieved scientific evidence entries.
        """
        extracted_claim_numbers = self._extract_numbers(claim_text)
        evidence_corpus_text = " ".join([e.get("summary", "") for e in retrieved_entries])
        evidence_numbers = self._extract_numbers(evidence_corpus_text)

        supported_numbers: List[str] = []
        unsupported_numbers: List[str] = []

        # Check each number in the claim
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

    def _extract_numbers(self, text: str) -> List[str]:
        """
        Extracts numbers, percentages, fractions, and ranges from text.
        """
        raw_matches = re.findall(r"\b(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?:\s*-\s*(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?))?\s*%?", text)
        
        cleaned = []
        for m in raw_matches:
            m_str = m.strip()
            # Ignore year numbers (e.g. 2018, 2024) or single-digit list numbers
            if any(re.match(p, m_str) for p in self.IGNORED_NUMBER_PATTERNS):
                continue
            if len(m_str) > 0:
                cleaned.append(m_str)
        return list(set(cleaned))

    def _is_number_supported(self, candidate_num: str, evidence_text: str, evidence_numbers: List[str]) -> bool:
        """
        Checks if candidate_num is directly present or mathematically encompassed in the evidence.
        """
        # Exact match
        if candidate_num in evidence_text:
            return True

        # Normalized match (strip % or commas)
        cand_clean = candidate_num.replace("%", "").replace(",", "").strip()
        for ev_num in evidence_numbers:
            ev_clean = ev_num.replace("%", "").replace(",", "").strip()
            if cand_clean == ev_clean:
                return True
            # Check range inclusion: e.g. "76" within "76-80"
            if "-" in ev_clean:
                parts = ev_clean.split("-")
                if len(parts) == 2 and cand_clean in [p.strip() for p in parts]:
                    return True

        return False

    def _rewrite_qualitatively(self, text: str, ungrounded_numbers: List[str]) -> str:
        """
        Converts ungrounded quantitative assertions into scientifically safe qualitative guidance.
        """
        rewritten = text
        for num in ungrounded_numbers:
            # Replace expressions like "by 48.5%" or "48.5%" with "substantially" or "measurably"
            rewritten = re.sub(rf"(?:by|at|around|approx(?:imately)?\s*)?{re.escape(num)}\s*%?", "substantially ", rewritten, flags=re.IGNORECASE)
            rewritten = re.sub(rf"\b{re.escape(num)}\b", "measurable ", rewritten)
        
        # Clean up double words and spacing
        rewritten = re.sub(r"\bsubstantially\s+substantially\b", "substantially", rewritten, flags=re.IGNORECASE)
        rewritten = re.sub(r"\s+", " ", rewritten).strip()
        return rewritten

claim_validator = ClaimValidator()

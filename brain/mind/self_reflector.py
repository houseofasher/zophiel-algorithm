"""
SELF REFLECTOR — Module 08 of the Zophiel Mind
Meta-cognition. Zophiel audits its own responses before delivery —
checking for bias, overconfidence, logical errors, and incomplete reasoning.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReflectionAudit:
    response_draft: str
    passed: bool
    confidence_calibrated: bool
    bias_flags: list[str]
    overstatements: list[str]
    missing_considerations: list[str]
    revised: str          # optionally revised response
    audit_score: float    # 0.0 = bad, 1.0 = excellent
    metadata: dict[str, Any] = field(default_factory=dict)


_OVERCONFIDENCE = re.compile(r'\b(definitely|certainly|absolutely|without doubt|always|never|impossible|guaranteed|proven fact)\b', re.I)
_HEDGE_OK       = re.compile(r'\b(likely|probably|suggests|may|might|appears|evidence indicates|research shows)\b', re.I)
_BIAS_SIGNALS   = {
    "anthropocentrism": re.compile(r'\b(humans are|mankind|for humanity|human progress)\b', re.I),
    "western_bias":     re.compile(r'\b(western|european|american|developed world)\b.{0,40}\b(standard|norm|ideal|model)\b', re.I),
    "recency_bias":     re.compile(r'\b(modern|recent|today|currently).{0,40}\b(better|superior|more advanced)\b', re.I),
    "authority_bias":   re.compile(r'\b(experts say|scientists agree|consensus is|official position)\b', re.I),
}
_MISSING_RE = {
    "no_counter_argument": re.compile(r'^(?!.*\b(however|but|although|on the other hand|counter|criticism|limitation|drawback)\b)', re.I),
    "no_uncertainty":      re.compile(r'^(?!.*\b(uncertain|unclear|debated|contested|unknown|open question)\b)', re.I),
}


class SelfReflector:
    """
    Before any response exits Zophiel, this module audits it.
    It asks: Is this calibrated? Is it honest? Is it complete?
    """

    def audit(self, draft: str, query: str = "") -> ReflectionAudit:
        overstatements = self._find_overstatements(draft)
        bias_flags     = self._find_bias(draft)
        missing        = self._find_missing(draft)
        calibrated     = len(overstatements) == 0
        score          = self._score(draft, overstatements, bias_flags, missing)
        passed         = score >= 0.6

        revised = draft
        if overstatements:
            revised = self._soften_overstatements(draft)

        return ReflectionAudit(
            response_draft=draft[:500],
            passed=passed,
            confidence_calibrated=calibrated,
            bias_flags=bias_flags,
            overstatements=overstatements,
            missing_considerations=missing,
            revised=revised,
            audit_score=score,
            metadata={"query_length": len(query), "response_length": len(draft)},
        )

    def _find_overstatements(self, text: str) -> list[str]:
        return [m.group(0) for m in _OVERCONFIDENCE.finditer(text)]

    def _find_bias(self, text: str) -> list[str]:
        return [name for name, pat in _BIAS_SIGNALS.items() if pat.search(text)]

    def _find_missing(self, text: str) -> list[str]:
        missing = []
        if not re.search(r'\b(however|but|although|on the other hand|counter|criticism|limitation)\b', text, re.I):
            missing.append("No counterargument or limitation acknowledged.")
        if len(text.split()) > 100 and not re.search(r'\b(uncertain|unclear|debated|unknown|open question)\b', text, re.I):
            missing.append("Uncertainty not acknowledged despite length.")
        return missing

    def _soften_overstatements(self, text: str) -> str:
        replacements = {
            "definitely": "likely",
            "certainly":  "in most cases",
            "absolutely": "generally",
            "always":     "typically",
            "never":      "rarely",
            "impossible": "highly unlikely",
            "guaranteed": "expected",
            "proven fact":"well-supported finding",
        }
        result = text
        for strong, soft in replacements.items():
            result = re.sub(r'\b' + strong + r'\b', soft, result, flags=re.I)
        return result

    def _score(self, text, overstatements, bias, missing) -> float:
        score = 1.0
        score -= len(overstatements) * 0.1
        score -= len(bias) * 0.08
        score -= len(missing) * 0.1
        if not _HEDGE_OK.search(text):
            score -= 0.1
        return max(0.0, min(1.0, score))

    def is_ready(self, draft: str) -> bool:
        return self.audit(draft).passed


_reflector = SelfReflector()

def audit(draft: str, query: str = "") -> ReflectionAudit:
    return _reflector.audit(draft, query)

def is_ready(draft: str) -> bool:
    return _reflector.is_ready(draft)

"""
LOGIC ENGINE — Module 07 of the Zophiel Mind
Logical reasoning over emotion. Evaluates arguments, detects fallacies,
builds inference chains, and scores claim credibility.
The smart mind is logical first, emotional never — unless emotion is the data.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogicResult:
    claim: str
    verdict: str               # "valid" | "invalid" | "uncertain" | "untestable"
    strength: float            # 0.0–1.0
    fallacies: list[str]
    inference_chain: list[str] # step-by-step reasoning
    assumptions: list[str]
    evidence_required: list[str]
    summary: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Formal fallacy patterns ───────────────────────────────────────────────────

FALLACIES = {
    "affirming_the_consequent": re.compile(r'\bif .+ then .+\b.{0,60}\btherefore\b.{0,60}\bif\b', re.I | re.S),
    "hasty_generalisation":     re.compile(r'\b(all|every|always|never|none|no one)\b.{0,60}\b(because|since|as)\b.{0,40}\bone\b', re.I),
    "slippery_slope":           re.compile(r'\b(lead to|result in|end in|eventually|inevitably|spiral).{0,80}(catastrophe|disaster|collapse|end)\b', re.I),
    "circular_reasoning":       re.compile(r'\b(because it is|obviously true|self-evident|goes without saying|everyone knows)\b', re.I),
    "false_equivalence":        re.compile(r'\b(just like|same as|equivalent to|no different from)\b', re.I),
    "straw_man":                re.compile(r'\b(so you\'re saying|what you mean is|in other words you believe)\b', re.I),
    "appeal_to_nature":         re.compile(r'\b(natural|nature|naturally occurring|organic).{0,30}(better|safer|healthier|good)\b', re.I),
    "post_hoc":                 re.compile(r'\b(after|following|since).{0,50}(therefore|caused|because|led to)\b', re.I),
}

# ── Credibility markers ───────────────────────────────────────────────────────

_STRONG_CLAIM = re.compile(r'\b(proves|proof|definitive|certain|absolute|fact|truth|undeniable|irrefutable)\b', re.I)
_HEDGE_CLAIM  = re.compile(r'\b(may|might|could|possibly|perhaps|suggests|indicates|appears|likely|unclear)\b', re.I)
_EVIDENCE_KW  = re.compile(r'\b(study|research|data|evidence|statistics|experiment|observation|measurement|trial)\b', re.I)
_ANECDOTE_KW  = re.compile(r'\b(I heard|someone told|a friend|in my experience|personally|I think|I feel|I believe)\b', re.I)

# ── Inference chain builder ───────────────────────────────────────────────────

_PREMISE_RE = re.compile(r'\b(because|since|given that|as|due to|owing to)\b(.{5,120}?)(?=[.,;]|$)', re.I)
_CONCLUSION_RE = re.compile(r'\b(therefore|thus|hence|so|consequently|it follows|we can conclude)\b(.{5,120}?)(?=[.,;]|$)', re.I)


class LogicEngine:
    """
    Logical analysis system. Fast, unemotional, thorough.
    Input: a claim or argument string.
    Output: verdict, fallacy list, inference chain.
    """

    def analyse(self, claim: str) -> LogicResult:
        fallacies      = self._detect_fallacies(claim)
        premises       = self._extract_premises(claim)
        conclusions    = self._extract_conclusions(claim)
        evidence_score = self._evidence_score(claim)
        strength       = self._strength_score(claim, fallacies, evidence_score)
        verdict        = self._verdict(strength, fallacies, claim)
        assumptions    = self._implicit_assumptions(claim)
        needs          = self._evidence_needed(claim, verdict)
        chain          = self._build_chain(premises, conclusions, verdict)
        summary        = self._summarise(verdict, strength, fallacies, chain)

        return LogicResult(
            claim=claim[:300],
            verdict=verdict,
            strength=strength,
            fallacies=fallacies,
            inference_chain=chain,
            assumptions=assumptions,
            evidence_required=needs,
            summary=summary,
            metadata={"evidence_score": evidence_score, "premise_count": len(premises)},
        )

    def _detect_fallacies(self, text: str) -> list[str]:
        found = []
        for name, pat in FALLACIES.items():
            if pat.search(text):
                found.append(name.replace('_', ' '))
        return found

    def _extract_premises(self, text: str) -> list[str]:
        return [m.group(2).strip() for m in _PREMISE_RE.finditer(text)][:5]

    def _extract_conclusions(self, text: str) -> list[str]:
        return [m.group(2).strip() for m in _CONCLUSION_RE.finditer(text)][:3]

    def _evidence_score(self, text: str) -> float:
        ev  = len(_EVIDENCE_KW.findall(text))
        anec = len(_ANECDOTE_KW.findall(text))
        return min(ev * 0.15 - anec * 0.1 + 0.3, 1.0)

    def _strength_score(self, text: str, fallacies: list, ev_score: float) -> float:
        strong = len(_STRONG_CLAIM.findall(text))
        hedge  = len(_HEDGE_CLAIM.findall(text))
        score  = ev_score - len(fallacies) * 0.15
        # Overclaiming without evidence weakens
        if strong > 0 and ev_score < 0.3:
            score -= 0.2
        # Appropriate hedging is a sign of intellectual honesty
        if hedge > 0:
            score += 0.05
        return max(0.0, min(1.0, score))

    def _verdict(self, strength: float, fallacies: list, text: str) -> str:
        if _STRONG_CLAIM.search(text) and len(fallacies) >= 2:
            return "invalid"
        if strength >= 0.6 and len(fallacies) == 0:
            return "valid"
        if strength >= 0.4:
            return "uncertain"
        if not _EVIDENCE_KW.search(text) and not _PREMISE_RE.search(text):
            return "untestable"
        return "uncertain"

    def _implicit_assumptions(self, text: str) -> list[str]:
        assumptions = []
        if _STRONG_CLAIM.search(text):
            assumptions.append("Assumes the claim can be proven with certainty.")
        if re.search(r'\bnatural\b', text, re.I):
            assumptions.append("Assumes 'natural' equals 'good' or 'correct'.")
        if re.search(r'\b(everyone|all people|humans naturally)\b', text, re.I):
            assumptions.append("Assumes universal applicability across all persons/contexts.")
        if _ANECDOTE_KW.search(text):
            assumptions.append("Generalises from personal or anecdotal experience.")
        return assumptions

    def _evidence_needed(self, text: str, verdict: str) -> list[str]:
        if verdict == "valid":
            return ["Replication studies to confirm findings.", "Peer review of supporting evidence."]
        return [
            "Empirical data from controlled observation or experiment.",
            "Independent verification of premises.",
            "Quantified effect size and confidence intervals.",
        ]

    def _build_chain(self, premises: list, conclusions: list, verdict: str) -> list[str]:
        chain = []
        for i, p in enumerate(premises, 1):
            chain.append(f"Premise {i}: {p}")
        if not premises:
            chain.append("Premise: [implicit — not explicitly stated]")
        for c in conclusions:
            chain.append(f"→ Conclusion: {c}")
        chain.append(f"→ Logical verdict: {verdict.upper()}")
        return chain

    def _summarise(self, verdict, strength, fallacies, chain) -> str:
        parts = [f"Verdict: {verdict.upper()} (strength {strength:.2f})."]
        if fallacies:
            parts.append(f"Fallacies detected: {', '.join(fallacies)}.")
        if len(chain) > 1:
            parts.append(f"Inference chain has {len(chain)} steps.")
        return " ".join(parts)

    def is_logical(self, text: str) -> bool:
        r = self.analyse(text)
        return r.verdict in ("valid", "uncertain") and len(r.fallacies) == 0

    def quick_score(self, text: str) -> float:
        return self.analyse(text).strength


# ── Singleton ─────────────────────────────────────────────────────────────────
_engine = LogicEngine()

def analyse(claim: str) -> LogicResult:
    return _engine.analyse(claim)

def quick_score(text: str) -> float:
    return _engine.quick_score(text)

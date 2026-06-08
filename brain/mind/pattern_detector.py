"""
PATTERN DETECTOR — Module 06 of the Zophiel Mind
Finds patterns quickly — both defensive (detecting threats, manipulation, deception)
and offensive (identifying opportunity, leverage, hidden structure).
Calm, fast, unemotional. Reads between the lines.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PatternReport:
    text: str
    detected: list[dict]          # [{name, type, confidence, excerpt}]
    threat_level: str             # "none" | "low" | "medium" | "high" | "critical"
    opportunity_signals: list[str]
    manipulation_flags: list[str]
    narrative_tags: list[str]
    summary: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Defensive patterns — deception, manipulation, propaganda ─────────────────

DEFENSIVE_PATTERNS = {
    # Logical fallacies
    "ad_hominem":        (re.compile(r'\b(stupid|idiot|moron|crazy|insane|lunatic|conspiracy theorist|uneducated)\b', re.I), "logical_fallacy"),
    "false_dichotomy":   (re.compile(r'\b(either|you\'re with us|you\'re against us|only two options|no other choice|must choose)\b', re.I), "logical_fallacy"),
    "appeal_to_authority": (re.compile(r'\b(experts say|scientists agree|officials confirm|studies show|research proves)\b', re.I), "rhetorical"),
    "emotional_manipulation": (re.compile(r'\b(you should be (afraid|scared|worried|concerned)|don\'t you care|think of the children|dangerous|urgent|crisis)\b', re.I), "manipulation"),
    "gaslighting":       (re.compile(r'\b(you\'re imagining|that never happened|you\'re overreacting|no one believes you|you misunderstood)\b', re.I), "manipulation"),
    "scarcity_urgency":  (re.compile(r'\b(limited time|act now|before it\'s too late|once in a lifetime|don\'t miss|only \d+ left)\b', re.I), "dark_pattern"),
    "social_proof":      (re.compile(r'\b(everyone is|everybody knows|most people|millions of|the consensus)\b', re.I), "rhetorical"),
    "false_authority":   (re.compile(r'\b(as a (doctor|scientist|expert|professor|insider|source) told me|I have it on good authority)\b', re.I), "deception"),
    "narrative_control": (re.compile(r'\b(misinformation|disinformation|fact.check|debunked|conspiracy|fringe|extremist)\b', re.I), "narrative"),
    "normalisation":     (re.compile(r'\b(this is normal|everyone does it|it\'s always been this way|that\'s just how it is)\b', re.I), "manipulation"),
}

# ── Offensive patterns — opportunity, leverage, hidden structure ──────────────

OPPORTUNITY_SIGNALS = {
    "information_asymmetry": re.compile(r'\b(few people know|little.known|hidden|secret|not widely reported|suppressed|classified)\b', re.I),
    "power_vacuum":          re.compile(r'\b(no one is leading|gap|nobody is addressing|vacuum|overlooked|neglected|ignored)\b', re.I),
    "emerging_trend":        re.compile(r'\b(emerging|growing|rise of|new wave|shift|transition|disruption|paradigm change)\b', re.I),
    "contradiction":         re.compile(r'\b(despite|however|yet|although|contradiction|paradox|inconsistency|anomaly)\b', re.I),
    "leverage_point":        re.compile(r'\b(key|critical|pivot|hinge|single point|bottleneck|fulcrum|crux|decisive)\b', re.I),
}

# ── Elite narrative markers ───────────────────────────────────────────────────

NARRATIVE_MARKERS = {
    "technocratic_control": re.compile(r'\b(digital ID|social credit|surveillance|tracking|monitoring|control grid|biometric)\b', re.I),
    "health_emergency":     re.compile(r'\b(pandemic|epidemic|public health emergency|mandatory|vaccination|biosecurity)\b', re.I),
    "climate_agenda":       re.compile(r'\b(carbon tax|net zero|15.minute city|rewilding|depopulation|sustainability agenda)\b', re.I),
    "financial_reset":      re.compile(r'\b(great reset|CBDC|digital currency|cashless|new world order|global governance)\b', re.I),
    "censorship_wave":      re.compile(r'\b(hate speech|deplatform|ban|silence|censor|remove|restrict|community guidelines)\b', re.I),
    "color_revolution":     re.compile(r'\b(protest|regime change|civil unrest|uprising|movement|grassroots|funding|NGO)\b', re.I),
}

_THREAT_THRESHOLDS = {"none": 0, "low": 1, "medium": 3, "high": 5, "critical": 8}


class PatternDetector:
    """
    Scans input for patterns — both dangers to be aware of and
    opportunities to be leveraged. Fast and non-reactive.
    """

    def scan(self, text: str) -> PatternReport:
        detected     : list[dict] = []
        manip_flags  : list[str]  = []
        narrative_tags: list[str] = []
        opp_signals  : list[str]  = []

        # Defensive scan
        for name, (pat, ptype) in DEFENSIVE_PATTERNS.items():
            matches = pat.findall(text)
            if matches:
                detected.append({
                    "name": name,
                    "type": ptype,
                    "confidence": min(0.5 + len(matches) * 0.1, 0.95),
                    "excerpt": matches[0] if matches else "",
                })
                if ptype == "manipulation":
                    manip_flags.append(name.replace('_', ' '))

        # Narrative scan
        for tag, pat in NARRATIVE_MARKERS.items():
            if pat.search(text):
                narrative_tags.append(tag.replace('_', ' '))

        # Offensive scan
        for sig, pat in OPPORTUNITY_SIGNALS.items():
            if pat.search(text):
                opp_signals.append(sig.replace('_', ' '))

        # Threat level
        threat_score = sum(1 for d in detected if d["type"] in ("manipulation","deception")) + len(narrative_tags)
        threat_level = "none"
        for level, threshold in sorted(_THREAT_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if threat_score >= threshold:
                threat_level = level
                break

        summary = self._summarise(detected, threat_level, narrative_tags, opp_signals)

        return PatternReport(
            text=text[:200],
            detected=detected,
            threat_level=threat_level,
            opportunity_signals=opp_signals,
            manipulation_flags=manip_flags,
            narrative_tags=narrative_tags,
            summary=summary,
            metadata={"pattern_count": len(detected), "threat_score": threat_score},
        )

    def _summarise(self, detected, threat, narratives, opps) -> str:
        parts = []
        if threat in ("high", "critical"):
            parts.append(f"⚠ High manipulation risk detected ({len(detected)} patterns).")
        elif threat == "medium":
            parts.append(f"Moderate rhetorical manipulation present ({len(detected)} patterns).")
        elif threat == "low":
            parts.append("Minor rhetorical patterns present.")
        else:
            parts.append("No significant manipulation patterns detected.")

        if narratives:
            parts.append(f"Narrative alignment with: {', '.join(narratives[:3])}.")
        if opps:
            parts.append(f"Opportunity signals: {', '.join(opps[:3])}.")
        return " ".join(parts)

    def quick_threat(self, text: str) -> str:
        """Fast single-call threat level check."""
        return self.scan(text).threat_level

    def extract_narrative(self, text: str) -> list[str]:
        """Return which elite narratives the text aligns with."""
        return [tag for tag, pat in NARRATIVE_MARKERS.items() if pat.search(text)]


# ── Singleton ─────────────────────────────────────────────────────────────────
_detector = PatternDetector()

def scan(text: str) -> PatternReport:
    return _detector.scan(text)

def quick_threat(text: str) -> str:
    return _detector.quick_threat(text)

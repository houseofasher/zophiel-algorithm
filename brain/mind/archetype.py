"""
ARCHETYPE — Module 05 of the Zophiel Mind
Classifies entities (persons, groups, ideas, events) against Jungian archetypes
and hermetic/occult frameworks. Every person and pattern is understood through
their archetypal signature before a response is formulated.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ArchetypeProfile:
    subject: str
    primary_archetype: str
    shadow_archetype: str
    hermetic_principle: str
    element: str           # fire, water, air, earth, aether
    polarity: str          # active/passive, solar/lunar
    trajectory: str        # ascending, descending, cyclical, static
    keywords: list[str]
    interpretation: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ── The 12 Jungian Archetypes ─────────────────────────────────────────────────

ARCHETYPES = {
    "Hero":         {"keywords": ["courage","struggle","overcome","victory","quest","warrior","fight","challenge","conquer","strength"], "shadow": "Tyrant", "element": "fire", "polarity": "active"},
    "Sage":         {"keywords": ["wisdom","knowledge","truth","understanding","insight","learn","teach","mentor","guide","enlighten"], "shadow": "Manipulator", "element": "air", "polarity": "active"},
    "Outlaw":       {"keywords": ["rebel","freedom","disrupt","destroy","revolution","break","rule","system","chaos","radical"], "shadow": "Nihilist", "element": "fire", "polarity": "active"},
    "Magician":     {"keywords": ["transform","power","vision","create","manifest","energy","change","alchemy","ritual","will"], "shadow": "Sorcerer", "element": "aether", "polarity": "active"},
    "Creator":      {"keywords": ["create","build","design","art","invent","make","innovate","expression","craft","vision"], "shadow": "Destroyer", "element": "earth", "polarity": "active"},
    "Explorer":     {"keywords": ["discover","freedom","journey","unknown","adventure","new","border","frontier","search","wanderer"], "shadow": "Drifter", "element": "air", "polarity": "active"},
    "Caregiver":    {"keywords": ["help","protect","nurture","support","heal","give","care","serve","compassion","sacrifice"], "shadow": "Martyr", "element": "water", "polarity": "passive"},
    "Ruler":        {"keywords": ["power","control","order","structure","authority","lead","command","govern","dominate","rule"], "shadow": "Dictator", "element": "earth", "polarity": "active"},
    "Innocent":     {"keywords": ["pure","simple","faith","trust","optimism","good","naive","hope","open","honest"], "shadow": "Victim", "element": "air", "polarity": "passive"},
    "Jester":       {"keywords": ["play","humour","fun","trick","entertain","joy","paradox","fool","light","absurd"], "shadow": "Deceiver", "element": "fire", "polarity": "passive"},
    "Lover":        {"keywords": ["passion","beauty","desire","connection","intimacy","pleasure","art","aesthetic","attract","bond"], "shadow": "Obsessive", "element": "water", "polarity": "passive"},
    "Everyman":     {"keywords": ["belong","community","common","people","ordinary","real","humble","practical","grounded","equal"], "shadow": "Conformist", "element": "earth", "polarity": "passive"},
}

# ── 7 Hermetic Principles (Kybalion) ──────────────────────────────────────────

HERMETIC_PRINCIPLES = {
    "Mentalism":    ["mind","thought","belief","consciousness","mental","idea","perception","reality","illusion"],
    "Correspondence": ["pattern","reflection","mirror","above","below","macro","micro","analogy","law","principle"],
    "Vibration":    ["frequency","energy","movement","oscillation","resonance","rhythm","wave","vibrate","sound","light"],
    "Polarity":     ["opposite","duality","tension","balance","contrast","positive","negative","yin","yang","paradox"],
    "Rhythm":       ["cycle","repeat","return","season","rise","fall","oscillate","pendulum","time","period"],
    "Cause_Effect": ["cause","effect","consequence","result","action","reaction","produce","follow","lead","chain"],
    "Gender":       ["masculine","feminine","active","passive","generate","create","receptive","initiate","complete"],
}

_PRINCIPLE_RE = {p: re.compile(r'\b(' + '|'.join(kws) + r')\b', re.I) for p, kws in HERMETIC_PRINCIPLES.items()}

_TRAJECTORIES = {
    re.compile(r'\b(rise|ascend|grow|expand|evolve|progress|advance|improve|elevate)\b', re.I): "ascending",
    re.compile(r'\b(fall|decline|decay|collapse|diminish|shrink|regress|deteriorate)\b', re.I): "descending",
    re.compile(r'\b(repeat|cycle|return|rotate|oscillate|recur|loop|revolve)\b', re.I): "cyclical",
    re.compile(r'\b(stable|static|fixed|unchanged|constant|persist|remain|sustain)\b', re.I): "static",
}


class ArchetypeClassifier:
    """
    Maps any subject (person, idea, movement, event) to its archetypal signature.
    Operates silently — the framework is implicit in every response Zophiel gives,
    not announced.
    """

    def classify(self, subject: str, context_text: str = "") -> ArchetypeProfile:
        text   = (subject + " " + context_text).lower()
        words  = set(re.findall(r'\b\w+\b', text))

        primary_arch, shadow = self._score_archetypes(text)
        hermetic = self._score_hermetic(text)
        element  = ARCHETYPES.get(primary_arch, {}).get("element", "aether")
        polarity = ARCHETYPES.get(primary_arch, {}).get("polarity", "active")
        traj     = self._detect_trajectory(text)
        kws      = ARCHETYPES.get(primary_arch, {}).get("keywords", [])[:5]

        interpretation = self._interpret(subject, primary_arch, shadow, hermetic, traj)

        return ArchetypeProfile(
            subject=subject,
            primary_archetype=primary_arch,
            shadow_archetype=shadow,
            hermetic_principle=hermetic,
            element=element,
            polarity=polarity,
            trajectory=traj,
            keywords=kws,
            interpretation=interpretation,
        )

    def _score_archetypes(self, text: str) -> tuple[str, str]:
        scores: dict[str, int] = {}
        for arch, data in ARCHETYPES.items():
            score = sum(1 for kw in data["keywords"] if re.search(r'\b' + kw + r'\b', text, re.I))
            scores[arch] = score
        primary = max(scores, key=scores.get) if any(scores.values()) else "Sage"
        shadow  = ARCHETYPES[primary]["shadow"]
        return primary, shadow

    def _score_hermetic(self, text: str) -> str:
        scores = {p: len(pat.findall(text)) for p, pat in _PRINCIPLE_RE.items()}
        return max(scores, key=scores.get) if any(scores.values()) else "Correspondence"

    def _detect_trajectory(self, text: str) -> str:
        for pat, traj in _TRAJECTORIES.items():
            if pat.search(text):
                return traj
        return "cyclical"

    def _interpret(self, subject, arch, shadow, hermetic, traj) -> str:
        return (
            f"'{subject}' expresses the {arch} archetype, whose shadow is the {shadow}. "
            f"The operative hermetic principle is {hermetic.replace('_',' ')}. "
            f"The current trajectory is {traj}. "
            f"Understanding this signature reveals the motivating forces at play and anticipates likely behaviour patterns."
        )

    def profile_from_text(self, text: str, subject: str | None = None) -> ArchetypeProfile:
        """Classify the dominant archetype present in a body of text."""
        subj = subject or text[:50].strip()
        return self.classify(subj, text)


# ── Singleton ─────────────────────────────────────────────────────────────────
_classifier = ArchetypeClassifier()

def classify(subject: str, context: str = "") -> ArchetypeProfile:
    return _classifier.classify(subject, context)

def profile_text(text: str) -> ArchetypeProfile:
    return _classifier.profile_from_text(text)

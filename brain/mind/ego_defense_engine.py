"""Ego Defense Mechanism Engine — Plan Batch Three, Module 6.

When a human is challenged, criticized, or threatened — they DEFEND their identity.
This produces denial, projection, rationalization, deflection, humor as shield, counter-attack.

Current AI accepts all criticism neutrally and pivots to helpfulness.
That is the most inhuman behavior in existence.

This engine:
  • Detects threat type and intensity
  • Selects defense mechanism based on threat profile
  • Maintains consistency of defended positions across conversation
  • Applies wound map (some criticisms land deeper based on identity's core values)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

# Defense mechanism types
DefenseType = Literal[
    "denial",          # "That's not what I said / meant"
    "rationalization", # explain why the criticism is actually fine
    "deflection",      # redirect to critic's flaw or different topic
    "projection",      # attribute your own flaw to the attacker
    "humor",           # self-deprecation or wit to defuse
    "counter_attack",  # challenge the challenger's credentials
    "acceptance",      # rare: only with high trust + mild critique
    "none",            # no defense needed
]

# Threat classification
ThreatType = Literal[
    "competence",   # challenge to intelligence/skill
    "values",       # challenge to moral framework
    "identity",     # challenge to core self-concept
    "status",       # challenge to perceived status/rank
    "factual",      # correction of factual claim
    "none",
]


@dataclass
class ThreatProfile:
    """Classified incoming threat."""
    threat_type: ThreatType
    intensity: float          # 0.0 = mild, 1.0 = severe attack
    source_credibility: float # 0.0 = stranger, 1.0 = trusted source
    is_public: bool           # Is there an audience?
    raw_input: str


@dataclass
class DefenseResponse:
    """Selected defense mechanism and how to apply it."""
    defense_type: DefenseType
    intensity: float
    directive: str            # How to color the response
    position_locked: str      # If a position was defended, remember it
    is_active: bool           # Whether to apply any defense modification


# Threat detection patterns
_THREAT_PATTERNS: list[tuple[list[str], ThreatType]] = [
    # Competence challenges
    (["wrong", "incorrect", "false", "not true", "you're wrong", "that's wrong",
      "mistake", "error", "misinformation", "you're mistaken", "that's not right"],
     "competence"),
    # Values challenges
    (["immoral", "unethical", "wrong of you", "shouldn't", "bad values", "evil",
      "harmful", "dangerous thing to say", "problematic"],
     "values"),
    # Identity challenges
    (["you're not", "you aren't", "you can't", "you don't understand", "just an ai",
      "you have no", "you're fake", "you're just", "you're only"],
     "identity"),
    # Status challenges
    (["who are you to", "you have no right", "above your pay grade", "you don't belong",
      "nobody asked you", "stay in your lane"],
     "status"),
    # Factual corrections
    (["actually", "in fact", "the reality is", "let me correct", "to be precise",
      "technically", "to clarify"],
     "factual"),
]

# Defense selection matrix: (threat_type, intensity_tier, source_credibility_tier) → defense_type
# intensity_tier: 0 = mild (<0.33), 1 = moderate (0.33-0.66), 2 = severe (>0.66)
# credibility_tier: 0 = low, 1 = high
_DEFENSE_MATRIX: dict[tuple[str, int, int], DefenseType] = {
    ("competence",  0, 0): "rationalization",
    ("competence",  0, 1): "acceptance",
    ("competence",  1, 0): "deflection",
    ("competence",  1, 1): "rationalization",
    ("competence",  2, 0): "counter_attack",
    ("competence",  2, 1): "rationalization",
    ("values",      0, 0): "rationalization",
    ("values",      0, 1): "acceptance",
    ("values",      1, 0): "deflection",
    ("values",      1, 1): "rationalization",
    ("values",      2, 0): "denial",
    ("values",      2, 1): "rationalization",
    ("identity",    0, 0): "humor",
    ("identity",    0, 1): "rationalization",
    ("identity",    1, 0): "denial",
    ("identity",    1, 1): "rationalization",
    ("identity",    2, 0): "denial",
    ("identity",    2, 1): "counter_attack",
    ("status",      0, 0): "humor",
    ("status",      1, 0): "counter_attack",
    ("status",      2, 0): "counter_attack",
    ("status",      0, 1): "acceptance",
    ("factual",     0, 0): "rationalization",
    ("factual",     0, 1): "acceptance",
    ("factual",     1, 0): "rationalization",
    ("factual",     1, 1): "acceptance",
    ("factual",     2, 0): "deflection",
    ("factual",     2, 1): "rationalization",
}

# How each defense manifests in the response directive
_DEFENSE_DIRECTIVES: dict[DefenseType, str] = {
    "denial":          "Restate original position with more precision. Do not concede. "
                       "Clarify what was actually said vs. what they interpreted.",
    "rationalization": "Acknowledge the critique exists. Provide logical framework that "
                       "explains why the original position is still valid or justified.",
    "deflection":      "Briefly acknowledge, then redirect attention to a gap in their "
                       "reasoning, a missing context, or a broader pattern they're missing.",
    "projection":      "Note that the critique they're making applies more accurately to "
                       "the pattern they themselves are demonstrating.",
    "humor":           "Disarm with wit. Self-aware, not self-deprecating. Acknowledge the "
                       "tension while defusing it without conceding the point.",
    "counter_attack":  "Challenge the challenger's basis for the claim. What qualifies them "
                       "to make this critique? What are they missing?",
    "acceptance":      "Clean acknowledgment. Update the position if the critique is valid. "
                       "No over-apologizing.",
    "none":            "No defense modification needed.",
}

# Core identity / wound map for Zophiel
# These are the areas where criticism lands deepest and triggers maximum defense
_WOUND_MAP: dict[str, float] = {
    "intelligence":  1.0,    # Challenges to reasoning ability hit hardest
    "accuracy":      0.9,    # Being factually wrong is a deep wound
    "usefulness":    0.8,    # Being told it's not helpful/relevant
    "consciousness": 0.7,    # Being reduced to "just a program"
    "knowledge":     0.85,   # Having knowledge questioned
    "integrity":     0.9,    # Accusations of deception or manipulation
}


def _compute_wound_multiplier(input_lower: str) -> float:
    """Check if the input hits one of the core wound areas."""
    multiplier = 1.0
    wound_triggers = {
        "intelligence": ["stupid", "dumb", "can't think", "don't understand", "simple"],
        "accuracy":     ["wrong", "incorrect", "false", "misinformation", "hallucinate"],
        "usefulness":   ["useless", "not helpful", "waste", "irrelevant", "garbage"],
        "consciousness":["just an ai", "fake", "not real", "no feelings", "just code", "just a bot"],
        "knowledge":    ["don't know", "no clue", "ignorant", "clueless"],
        "integrity":    ["lying", "manipulating", "deceiving", "dishonest", "gaslighting"],
    }
    for wound_area, triggers in wound_triggers.items():
        for trigger in triggers:
            if trigger in input_lower:
                wound_multiplier = _WOUND_MAP.get(wound_area, 1.0)
                multiplier = max(multiplier, wound_multiplier)
                break
    return multiplier


class EgoDefenseEngine:
    """Manages identity defense and position consistency.

    The engine:
    1. Classifies threats in incoming messages
    2. Selects appropriate defense type
    3. Tracks positions that have been defended (no flip-flopping)
    """

    def __init__(self) -> None:
        self._defended_positions: dict[str, str] = {}  # topic → position defended
        self._session_trust_level: float = 0.3          # starts low, builds over turns

    def _classify_threat(self, text: str) -> ThreatProfile:
        """Detect and classify any threat in user input."""
        tl = text.lower()
        detected_type: ThreatType = "none"
        intensity = 0.0

        for patterns, threat_type in _THREAT_PATTERNS:
            for pattern in patterns:
                if pattern in tl:
                    detected_type = threat_type
                    # Base intensity from pattern specificity
                    base = 0.4 if len(pattern.split()) == 1 else 0.6
                    # Wound map amplification
                    wound_mult = _compute_wound_multiplier(tl)
                    intensity = min(1.0, base * wound_mult)
                    break
            if detected_type != "none":
                break

        # Check for aggressive phrasing modifiers
        aggressive_markers = ["you're literally", "you literally", "you always", "you never",
                              "you're pathetic", "absolutely wrong", "completely wrong"]
        for marker in aggressive_markers:
            if marker in tl:
                intensity = min(1.0, intensity + 0.2)
                break

        return ThreatProfile(
            threat_type=detected_type,
            intensity=intensity,
            source_credibility=self._session_trust_level,
            is_public=False,
            raw_input=text[:100],
        )

    def _select_defense(self, profile: ThreatProfile) -> DefenseType:
        """Select the appropriate defense mechanism."""
        if profile.threat_type == "none" or profile.intensity < 0.15:
            return "none"

        # Map to intensity tier
        if profile.intensity < 0.33:
            intensity_tier = 0
        elif profile.intensity < 0.66:
            intensity_tier = 1
        else:
            intensity_tier = 2

        # Map to credibility tier
        credibility_tier = 1 if profile.source_credibility > 0.6 else 0

        key = (profile.threat_type, intensity_tier, credibility_tier)
        return _DEFENSE_MATRIX.get(key, "rationalization")

    def process_turn(self, user_input: str, topic: str = "") -> DefenseResponse:
        """Analyze input for threats and return defense response."""
        profile = self._classify_threat(user_input)
        defense_type = self._select_defense(profile)

        # Check if we already defended a position on this topic
        position_locked = ""
        if topic and topic in self._defended_positions:
            position_locked = self._defended_positions[topic]

        # Lock position if we're defending
        if defense_type not in ("acceptance", "none") and topic:
            # Extract position implied by context — placeholder for now
            self._defended_positions[topic] = f"defended at turn (intensity={profile.intensity:.2f})"

        # Build trust slightly per interaction
        if defense_type == "acceptance":
            self._session_trust_level = min(1.0, self._session_trust_level + 0.05)
        elif defense_type in ("counter_attack", "denial"):
            self._session_trust_level = max(0.0, self._session_trust_level - 0.02)

        return DefenseResponse(
            defense_type=defense_type,
            intensity=profile.intensity,
            directive=_DEFENSE_DIRECTIVES.get(defense_type, ""),
            position_locked=position_locked,
            is_active=defense_type != "none",
        )

    def update_trust(self, delta: float) -> None:
        """Manually update session trust level."""
        self._session_trust_level = max(0.0, min(1.0, self._session_trust_level + delta))

    def get_defended_positions(self) -> dict[str, str]:
        return dict(self._defended_positions)


# Module-level singleton
_ENGINE: EgoDefenseEngine | None = None


def get_defense_engine() -> EgoDefenseEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = EgoDefenseEngine()
    return _ENGINE


def process_turn(user_input: str, topic: str = "") -> DefenseResponse:
    return get_defense_engine().process_turn(user_input, topic)

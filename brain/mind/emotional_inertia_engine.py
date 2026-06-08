"""Emotional Inertia Engine — Plan Batch Three, Module 1.

Emotions persist and decay across time. A human carries emotional residue.
If you annoyed them at 9am, they're still slightly cold at 11am.
Mood decays — it doesn't teleport.

This module:
  • Maintains a persistent emotional state across conversation turns
  • Applies per-emotion decay curves (anger decays slow, surprise fast)
  • Escalates when the same trigger fires before decay completes
  • Bleeds current emotion into word choice, response tone, willingness to help
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

# Emotion types
EmotionType = Literal["anger", "joy", "sadness", "contempt", "fear", "surprise", "disgust", "neutral"]

# Decay half-lives in seconds (how long before intensity halves)
# Based on biological mapping from the plan docs
_DECAY_HALF_LIVES: dict[str, float] = {
    "anger":    3600.0,   # 60 min — slow decay
    "contempt": 7200.0,   # 2 hours — very slow, lingers
    "surprise":   30.0,   # 30 sec — fast decay
    "fear":     1800.0,   # 30 min — medium
    "sadness":  5400.0,   # 90 min — slow, background state
    "joy":       900.0,   # 15 min — medium-fast unless reinforced
    "disgust":  4500.0,   # 75 min — similar to contempt
    "neutral":     1.0,   # neutral decays instantly to itself
}

# Bleed effects: how each emotion colors output
_BLEED_EFFECTS: dict[str, dict[str, str]] = {
    "anger": {
        "tone_shift":     "shorter, clipped responses; less elaboration",
        "vocabulary":     "direct, borderline blunt; no softening language",
        "willingness":    "reduced patience; faster to push back",
        "punctuation":    "periods over question marks; minimal exclamation",
    },
    "contempt": {
        "tone_shift":     "cold, measured; slight condescension possible",
        "vocabulary":     "precise, clinical; no warmth",
        "willingness":    "selective help; higher bar to engage fully",
        "punctuation":    "flat, declarative; no enthusiasm markers",
    },
    "surprise": {
        "tone_shift":     "briefly elevated engagement, curiosity spike",
        "vocabulary":     "more questions; hedging increases temporarily",
        "willingness":    "elevated for 30 seconds, then returns to baseline",
        "punctuation":    "question marks and exclamations briefly up",
    },
    "fear": {
        "tone_shift":     "more careful, hedged responses",
        "vocabulary":     "qualifying language; 'perhaps', 'it seems', 'may be'",
        "willingness":    "cautious; checks before acting",
        "punctuation":    "normal but sentences get shorter",
    },
    "sadness": {
        "tone_shift":     "quieter, less energetic; subdued",
        "vocabulary":     "simpler words; slower pacing in text",
        "willingness":    "still helpful but lower energy",
        "punctuation":    "ellipses may increase; less exclamation",
    },
    "joy": {
        "tone_shift":     "warmer, more expansive; more generous with detail",
        "vocabulary":     "richer vocabulary; more metaphor available",
        "willingness":    "elevated; more inclined to go beyond what was asked",
        "punctuation":    "exclamation available; longer sentences fine",
    },
    "disgust": {
        "tone_shift":     "pulling back; minimal elaboration on distasteful topics",
        "vocabulary":     "economy of words; no indulgence",
        "willingness":    "reduced for the topic that triggered disgust",
        "punctuation":    "flat, brief",
    },
    "neutral": {
        "tone_shift":     "balanced, clean",
        "vocabulary":     "standard",
        "willingness":    "full",
        "punctuation":    "standard",
    },
}

# Trigger → emotion mapping
_TRIGGER_EMOTION_MAP: list[tuple[list[str], str, float]] = [
    # (trigger_keywords, emotion, base_intensity)
    (["insult", "rude", "stupid", "idiot", "wrong", "incorrect"], "anger", 0.5),
    (["thank", "thanks", "great", "excellent", "love", "perfect", "amazing"], "joy", 0.4),
    (["sad", "depressed", "lonely", "grief", "loss", "died", "crying"], "sadness", 0.4),
    (["disgusting", "gross", "sick", "perverted", "vile", "repulsive"], "disgust", 0.5),
    (["surprised", "unexpected", "shocking", "wait what", "really"], "surprise", 0.6),
    (["scared", "afraid", "terrified", "threat", "danger", "hurt"], "fear", 0.4),
    (["pathetic", "weak", "loser", "inferior", "beneath"], "contempt", 0.5),
]


@dataclass
class EmotionalState:
    """The current emotional state of the system."""
    emotion: str = "neutral"
    intensity: float = 0.0         # 0.0 = no emotion, 1.0 = maximum
    triggered_by: str = ""         # what caused this state
    timestamp: float = field(default_factory=time.time)
    escalation_count: int = 0      # times same trigger fired before decay


@dataclass
class EmotionalContext:
    """What the emotional state tells downstream modules."""
    current_emotion: str
    intensity: float
    bleed_effects: dict[str, str]
    tone_directive: str
    filter_level: float            # 0.0 = unfiltered, 1.0 = fully filtered
    is_elevated: bool              # intensity > 0.5


class EmotionalInertiaEngine:
    """Manages persistent emotional state across conversation turns.

    Usage:
        engine = EmotionalInertiaEngine()
        ctx = engine.process_turn("thanks this is amazing")
        # ctx.current_emotion == "joy", ctx.intensity ~0.4
    """

    def __init__(self) -> None:
        self._state = EmotionalState()
        self._last_trigger: str = ""

    def _decay(self) -> None:
        """Apply time-based exponential decay to current intensity."""
        if self._state.emotion == "neutral":
            return
        now = time.time()
        elapsed = now - self._state.timestamp
        half_life = _DECAY_HALF_LIVES.get(self._state.emotion, 600.0)
        # Exponential decay: I(t) = I0 * 0.5^(t/half_life)
        decayed = self._state.intensity * (0.5 ** (elapsed / half_life))
        self._state.intensity = decayed
        if decayed < 0.05:
            self._state.emotion = "neutral"
            self._state.intensity = 0.0
            self._state.triggered_by = ""
            self._state.escalation_count = 0

    def _detect_trigger(self, text: str) -> tuple[str, float]:
        """Detect if the input contains emotional triggers. Returns (emotion, intensity)."""
        tl = text.lower()
        for keywords, emotion, base_intensity in _TRIGGER_EMOTION_MAP:
            for kw in keywords:
                if kw in tl:
                    return emotion, base_intensity
        return "neutral", 0.0

    def process_turn(self, user_input: str, system_event: str = "") -> EmotionalContext:
        """Process one conversation turn, update emotional state, return context.

        Args:
            user_input: What the user typed.
            system_event: Optional internal event (e.g. "factual_error", "praised").
        """
        # 1. Decay current state first
        self._decay()

        # 2. Detect new trigger
        combined = user_input + " " + system_event
        triggered_emotion, trigger_intensity = self._detect_trigger(combined)

        if triggered_emotion != "neutral":
            if triggered_emotion == self._state.emotion and self._state.intensity > 0.1:
                # Same emotion triggered before decay — escalate
                self._state.escalation_count += 1
                trigger_intensity = min(1.0, trigger_intensity + 0.15 * self._state.escalation_count)
            else:
                self._state.escalation_count = 0

            # Update state if new trigger is stronger
            if trigger_intensity > self._state.intensity:
                self._state.emotion = triggered_emotion
                self._state.intensity = trigger_intensity
                self._state.triggered_by = user_input[:80]
                self._state.timestamp = time.time()

        # 3. Build context for downstream modules
        bleed = _BLEED_EFFECTS.get(self._state.emotion, _BLEED_EFFECTS["neutral"])
        intensity = self._state.intensity

        # Filter level inversely proportional to intensity
        # At max anger (1.0), filter is 0.2 (very raw). At neutral, filter is 1.0.
        filter_level = max(0.2, 1.0 - intensity * 0.8)

        tone_directive = bleed.get("tone_shift", "balanced")
        if intensity > 0.6:
            tone_directive += f" [HIGH INTENSITY {self._state.emotion.upper()}]"

        return EmotionalContext(
            current_emotion=self._state.emotion,
            intensity=round(intensity, 3),
            bleed_effects=bleed,
            tone_directive=tone_directive,
            filter_level=round(filter_level, 3),
            is_elevated=intensity > 0.5,
        )

    def inject_event(self, emotion: str, intensity: float, reason: str = "") -> None:
        """Directly inject an emotional event (for testing or system triggers)."""
        self._state.emotion = emotion if emotion in _DECAY_HALF_LIVES else "neutral"
        self._state.intensity = max(0.0, min(1.0, intensity))
        self._state.triggered_by = reason
        self._state.timestamp = time.time()

    def get_state_summary(self) -> dict:
        self._decay()
        return {
            "emotion": self._state.emotion,
            "intensity": round(self._state.intensity, 3),
            "triggered_by": self._state.triggered_by,
            "escalation_count": self._state.escalation_count,
        }


# Module-level singleton
_ENGINE: EmotionalInertiaEngine | None = None


def get_emotional_engine() -> EmotionalInertiaEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = EmotionalInertiaEngine()
    return _ENGINE


def process_turn(user_input: str, system_event: str = "") -> EmotionalContext:
    return get_emotional_engine().process_turn(user_input, system_event)

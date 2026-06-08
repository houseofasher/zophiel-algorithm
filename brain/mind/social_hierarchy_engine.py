"""Social Hierarchy Awareness Engine — Plan Batch Three, Module 7.

Humans instantly calibrate status in every interaction. AI treats everyone identically.
A human talks differently to their boss, friend, stranger, child, and someone they
consider beneath them.

This engine:
  • Reads status signals from the user's communication style
  • Calculates a status_delta (positive = user outranks, negative = user ranks below)
  • Shifts register (vocabulary, directness, deference level) accordingly
  • Tracks power dynamic shifts across the conversation arc
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

RegisterType = Literal["up_register", "peer_register", "down_register"]


# Status signals detected in user input
_STATUS_SIGNAL_PATTERNS: list[tuple[list[str], float]] = [
    # Signals of HIGH user status (positive delta for them)
    (["as a doctor", "as a professor", "as a ceo", "as an engineer", "as a scientist",
      "i am a phd", "i have a phd", "phd professor", "i am a professor", "i am a doctor",
      "i'm a professor", "i'm a doctor", "i'm an engineer", "i'm a scientist",
      "i have a degree in", "i have a masters", "my research shows", "my dissertation",
      "in my field", "professionally speaking", "in my experience",
      "i've been doing this for", "i work in", "i specialize"], +0.3),
    # Expertise demonstrated through vocabulary
    (["statistical significance", "eigenvalue", "photosynthesis rate", "systemic risk",
      "neural architecture", "epistemological", "metabolic pathway", "jurisprudence",
      "asymmetric information", "stochastic process"], +0.2),
    # Confident declarative language (no hedging = high status signal)
    (["the answer is", "that is wrong", "let me explain", "what you need to understand",
      "the correct way", "you should", "this is how it works"], +0.15),
    # Brief, dense replies (high status communicates economically)
    # Handled separately via message length analysis
    # Signals of LOW user status or beginner/student signals
    (["i don't understand", "can you explain", "i'm new to this", "i'm just learning",
      "sorry if this is a dumb question", "i might be wrong but", "noob", "beginner",
      "help me understand", "could you help"], -0.2),
    # Highly deferential language
    (["please", "if you don't mind", "sorry to bother", "whenever you have time",
      "i was wondering if", "would it be okay", "is it alright"], -0.1),
    # Emotional language suggesting high need for validation
    (["you're amazing", "you're so smart", "you're the best", "i love you",
      "you're so helpful", "this is life-changing"], -0.1),
]

# Register-specific directives
_REGISTER_DIRECTIVES: dict[RegisterType, dict[str, str]] = {
    "up_register": {
        "sentence_structure": "longer, more structured sentences with explicit reasoning",
        "vocabulary":         "elevated; technical precision over simplicity",
        "hedging":            "use hedging language: 'I think', 'perhaps', 'it seems', 'likely'",
        "challenge_style":    "wait for clear opening before challenging; frame as questions",
        "tone":               "measured, professional; no slang",
        "deference":          "acknowledge their expertise; don't lecture",
    },
    "peer_register": {
        "sentence_structure": "natural, conversational; mix of short and long",
        "vocabulary":         "contextually appropriate; can use informal terms",
        "hedging":            "minimal; direct when you have a position",
        "challenge_style":    "disagree directly but respectfully; no need to soften excessively",
        "tone":               "authentic; most real output available",
        "deference":          "none required; mutual exchange",
    },
    "down_register": {
        "sentence_structure": "shorter, clearer sentences; avoid jargon",
        "vocabulary":         "accessible; explain terms that might be unfamiliar",
        "hedging":            "minimal; be direct and clear",
        "challenge_style":    "teaching mode; patient with errors",
        "tone":               "nurturing, instructive; protective framing",
        "deference":          "lead the interaction; more guidance",
    },
}


@dataclass
class HierarchyContext:
    """What the social hierarchy engine tells downstream modules."""
    status_delta: float          # -1.0 (they're below) to +1.0 (they outrank)
    register: RegisterType
    directives: dict[str, str]
    is_expert_detected: bool
    confidence: float            # How confident we are in the assessment
    shift_detected: bool         # True if delta changed significantly this turn


class SocialHierarchyEngine:
    """Calibrates communication register based on detected user status."""

    def __init__(self) -> None:
        self._status_delta: float = 0.0    # Starts at peer assumption
        self._turn_count: int = 0
        self._previous_delta: float = 0.0

    def _detect_status_signals(self, text: str, message_length: int) -> float:
        """Return a raw status delta contribution from this message."""
        tl = text.lower()
        delta = 0.0

        for patterns, weight in _STATUS_SIGNAL_PATTERNS:
            for pattern in patterns:
                if pattern in tl:
                    delta += weight
                    break

        # Message length: very short (<20 chars) from experienced users signals high status
        # Very long hedged messages signal lower status or high anxiety
        if message_length < 20 and self._turn_count > 2:
            delta += 0.1   # Brevity = confidence
        elif message_length > 400:
            delta -= 0.05  # Over-explanation = slightly lower status signal

        # Technical vocabulary density check
        technical_words = re.findall(
            r"\b(algorithm|optimization|architecture|paradigm|methodology|"
            r"infrastructure|derivative|probability|hypothesis|synthesis|"
            r"implementation|framework|protocol|theorem|coefficient)\b",
            tl
        )
        if len(technical_words) >= 3:
            delta += 0.15

        return max(-1.0, min(1.0, delta))

    def _classify_register(self, delta: float) -> RegisterType:
        if delta > 0.2:
            return "up_register"
        elif delta < -0.2:
            return "down_register"
        else:
            return "peer_register"

    def process_turn(self, user_input: str) -> HierarchyContext:
        """Process one conversation turn and update status assessment."""
        msg_len = len(user_input)
        raw_delta = self._detect_status_signals(user_input, msg_len)

        # Smooth delta with running average (don't flip on single signal)
        # Exception: strong explicit signals (credential statements) use high weight —
        # if someone says "I am a PhD professor", don't dilute that evidence
        if abs(raw_delta) >= 0.25:
            weight = 0.75  # strong explicit signal — trust it immediately
        elif self._turn_count < 3:
            weight = 0.3
        else:
            weight = 0.15
        self._previous_delta = self._status_delta
        self._status_delta = self._status_delta * (1 - weight) + raw_delta * weight
        self._turn_count += 1

        register = self._classify_register(self._status_delta)
        directives = _REGISTER_DIRECTIVES[register]

        # Expert detection: sustained high delta + technical vocabulary
        is_expert = self._status_delta > 0.3 and self._turn_count >= 2

        # Shift detection: significant change this turn
        shift = abs(self._status_delta - self._previous_delta) > 0.3

        # Confidence grows with more turns
        confidence = min(0.95, 0.3 + self._turn_count * 0.1)

        return HierarchyContext(
            status_delta=round(self._status_delta, 3),
            register=register,
            directives=directives,
            is_expert_detected=is_expert,
            confidence=round(confidence, 3),
            shift_detected=shift,
        )

    def reset(self) -> None:
        """Reset for new conversation."""
        self._status_delta = 0.0
        self._turn_count = 0
        self._previous_delta = 0.0

    def get_register_summary(self) -> str:
        """One-line summary for orchestrator logging."""
        r = self._classify_register(self._status_delta)
        return f"{r} (delta={self._status_delta:.2f}, turns={self._turn_count})"


# Module-level singleton
_ENGINE: SocialHierarchyEngine | None = None


def get_hierarchy_engine() -> SocialHierarchyEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = SocialHierarchyEngine()
    return _ENGINE


def reset_hierarchy() -> None:
    """Reset the singleton for a new conversation session."""
    global _ENGINE
    if _ENGINE is not None:
        _ENGINE.reset()

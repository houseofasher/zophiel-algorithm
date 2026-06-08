"""Canonical fallback reply strings — imported everywhere in chat_service."""

from __future__ import annotations

import os

# ------------------------------------------------------------------
# Fallback message constants
# ------------------------------------------------------------------

FALLBACK_TRAINING = (
    "I'm still building knowledge in this area. "
    "My learning pipeline is running — check back after more training cycles."
)

FALLBACK_CORPUS = (
    "I don't have verified information on this topic in my corpus yet. "
    "I can reason from first principles, or you can ask me something I've trained on."
)

FALLBACK_TIMEOUT = (
    "That question took longer than expected to process. "
    "Try a more specific question or rephrase."
)

FALLBACK_PHILOSOPHY = (
    "That's a deep question — one I hold as genuinely open. "
    "I can walk through different frameworks if that's useful."
)

ECHO_DETECTED_REPLY = (
    "I noticed that might be an echo of something I said. "
    "What would you like to explore next?"
)

SELF_ECHO_DETECTED_REPLY = (
    "That looks like something from my own output. "
    "What's the actual question?"
)

RATE_LIMIT_PREDICT = (
    "Too many requests right now — please wait a moment and try again."
)


def still_training_reply(domain: str | None = None) -> str:
    if domain:
        return (
            f"I'm still training on {domain.replace('_', ' ')}. "
            "More cycles needed before I can give a reliable answer."
        )
    return FALLBACK_TRAINING


# ------------------------------------------------------------------
# System echo detection
# ------------------------------------------------------------------

_ECHO_PHRASES = (
    "i am aureon",
    "my architecture runs",
    "sovereign intelligence",
    "zophiel doctrine",
    "six-region learning",
    "backpropagation trainer",
)


def is_system_echo(text: str) -> bool:
    """True if the message looks like the user pasted Aureon's own output back."""
    lower = text.strip().lower()
    matches = sum(1 for phrase in _ECHO_PHRASES if phrase in lower)
    return matches >= 2

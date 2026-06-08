"""Psychology brain — shapes HOW Aureon responds (tone, pacing, clarifiers).

Based on Human Psychology Brain + Human Emotions + Text Human Patterns docs.
This layer wraps the algorithm brain's output in human-shaped communication.
"""

from __future__ import annotations

import re
from typing import Any

_VAGUE_BROAD = re.compile(
    r"^(tell me (about|everything about)|explain|what (is|are)|describe)\s+\w{1,12}\??$",
    re.I,
)

_CLARIFIER_SIGNALS = (
    "what do you mean",
    "more about",
    "go on",
    "keep going",
    "say more",
    "like what",
    "for example",
    "such as",
)

_TONE_MAP = {
    "philosophy": "reflective",
    "identity": "grounded",
    "predict": "analytical",
    "simple_qa": "direct",
    "search_opinion": "evidence_based",
    "chat": "conversational",
    "code": "technical",
}


def _detect_mode(payload: dict[str, Any], user: str) -> str:
    kind = str(payload.get("kind", "chat"))
    if kind in _TONE_MAP:
        return kind
    q = user.lower()
    if any(s in q for s in _CLARIFIER_SIGNALS):
        return "clarifier"
    if _VAGUE_BROAD.match(q.strip()):
        return "curious_clarifier"
    return "chat"


def _build_traits(mode: str, payload: dict[str, Any]) -> list[str]:
    traits: list[str] = []
    if payload.get("ciper"):
        traits.append("marie_ciper_logic")
    if payload.get("sources"):
        traits.append("evidence_cited")
    if mode == "curious_clarifier":
        traits.append("social_clarification")
    if mode in ("philosophy", "identity"):
        traits.append("honest_uncertainty")
    return traits


def finalize_chat_payload(
    payload: dict[str, Any],
    user_message: str,
) -> dict[str, Any]:
    """Add psychology layer to the assembled payload before returning to caller."""
    mode = _detect_mode(payload, user_message)
    traits = _build_traits(mode, payload)

    payload["psychology"] = {
        "mode": mode,
        "tone": _TONE_MAP.get(mode, "conversational"),
        "traits": traits,
    }
    payload["brains"] = {
        "psychology": "response_layer — how Aureon acts human",
        "algorithm": "six_regions — collector, verifier, labeler, trainer, evaluator, reward",
    }

    # Clean up any classification leaks in reply
    reply = str(payload.get("reply", ""))
    reply = re.sub(r"\b[a-z_]+\.[a-z_]+\.[a-z_]+\b", "", reply).strip()
    if reply:
        payload["reply"] = reply

    return payload

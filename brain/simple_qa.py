"""Simple Q&A — short factual questions get short factual answers from corpus."""

from __future__ import annotations

import re
from typing import Any

_SHORT_QUESTION = re.compile(r"^[^?]{1,60}\?$")
_FACT_STARTERS = (
    "what is ",
    "what are ",
    "who is ",
    "who was ",
    "when was ",
    "when did ",
    "where is ",
    "how many ",
    "define ",
    "what does ",
    "what's ",
)


def is_simple_question(text: str) -> bool:
    """True if the message is a short direct factual question."""
    q = text.strip().lower()
    if len(q) > 120:
        return False
    if not q.endswith("?"):
        return False
    return any(q.startswith(s) for s in _FACT_STARTERS)


def to_simple_answer(text: str, max_len: int = 300, corpus_hits: list[str] | None = None) -> dict[str, Any] | None:
    """Try to build a short answer from corpus_hits or return None."""
    if not corpus_hits:
        return None
    # Pick the most relevant sentence from the first hit
    first = corpus_hits[0]
    sentences = re.split(r"(?<=[.!?])\s+", first)
    best = max(sentences, key=lambda s: len(s.split()), default="")
    if len(best.split()) < 5:
        return None
    return {
        "reply": best.strip(),
        "kind": "simple_qa",
        "simple_qa": True,
    }

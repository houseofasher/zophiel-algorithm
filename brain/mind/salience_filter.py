"""
Salience / Attention Filter — Decides what matters in a message.
Scores sentences by importance, flags the most salient span,
and suppresses noise (filler, pleasantries, repetition).
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field

_NOISE = re.compile(
    r'^(hello|hi|hey|thanks|thank you|ok|okay|sure|alright|please|'
    r'can you|could you|would you|i want|i need|tell me|explain)[,\s]',
    re.IGNORECASE,
)
_SIGNAL_WORDS = {
    'define','explain','how','why','what','when','where','who','which',
    'difference','compare','cause','effect','mechanism','prove','calculate',
    'list','describe','analyse','evaluate','criticise','contrast',
}

@dataclass
class SalienceResult:
    core_query: str            # most informative span
    noise_removed: str         # input with filler stripped
    signal_words: list[str]    # high-info trigger words found
    salience_score: float      # 0-1
    is_trivial: bool           # True if input is almost all noise

def filter_salience(text: str) -> SalienceResult:
    # Strip leading pleasantries
    cleaned = _NOISE.sub('', text).strip()
    if not cleaned:
        cleaned = text.strip()

    # Tokenise
    words = re.findall(r'\b\w+\b', cleaned.lower())
    hits = [w for w in words if w in _SIGNAL_WORDS]

    # Score: signal word density + length bonus
    score = min(len(hits) / max(len(words), 1) * 3 + (0.1 if len(words) > 8 else 0), 1.0)

    # Core query: first sentence or first 120 chars, whichever is shorter
    first_sent = re.split(r'[.!?]', cleaned)[0].strip()
    core = first_sent[:120] if first_sent else cleaned[:120]

    return SalienceResult(
        core_query=core,
        noise_removed=cleaned,
        signal_words=hits,
        salience_score=round(score, 3),
        is_trivial=(score < 0.05 and len(words) < 5),
    )

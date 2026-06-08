"""
Contradiction Handler — Detects and resolves internal contradictions.
Scans a candidate answer (or a list of retrieved passages) for logically
inconsistent claims, flags them, and attempts a resolution strategy.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field

_NEGATION = re.compile(r'\b(not|no|never|cannot|can\'t|isn\'t|aren\'t|doesn\'t|won\'t|neither|nor)\b', re.I)
_QUANTITY_RE = re.compile(r'\b(\d[\d.,]*)\s*(%|km|kg|m|years?|days?|seconds?|°[CF]|eV|MeV|GeV)\b')

@dataclass
class Contradiction:
    span_a: str
    span_b: str
    reason: str

@dataclass
class ContradictionReport:
    contradictions: list[Contradiction]
    resolved_text: str
    has_conflict: bool
    confidence_penalty: float   # subtract from confidence when conflict found

def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 10]

def _polarity(sent: str) -> int:
    """Count negations — odd = negative polarity, even = positive."""
    return len(_NEGATION.findall(sent)) % 2

def check_contradictions(text: str, passages: list[str] | None = None) -> ContradictionReport:
    sents = _sentences(text)
    all_sents = sents + (passages or [])

    conflicts: list[Contradiction] = []

    # Rule 1: same subject, opposite polarity
    for i, a in enumerate(all_sents):
        for b in all_sents[i+1:]:
            # Rough subject match: first 3 significant words
            a_sig = re.sub(r'\b(a|an|the|is|are|was|were|of)\b', '', a.lower()).split()[:3]
            b_sig = re.sub(r'\b(a|an|the|is|are|was|were|of)\b', '', b.lower()).split()[:3]
            overlap = set(a_sig) & set(b_sig)
            if len(overlap) >= 2 and _polarity(a) != _polarity(b):
                conflicts.append(Contradiction(
                    span_a=a[:80],
                    span_b=b[:80],
                    reason='opposite polarity on same subject',
                ))

    # Rule 2: numeric conflicts (same unit, very different magnitudes)
    nums: list[tuple[float, str, str]] = []
    for s in all_sents:
        for m in _QUANTITY_RE.finditer(s):
            try:
                nums.append((float(m.group(1).replace(',', '')), m.group(2), s[:80]))
            except ValueError:
                pass
    for i, (va, unit_a, sa) in enumerate(nums):
        for vb, unit_b, sb in nums[i+1:]:
            if unit_a == unit_b and va > 0 and vb > 0:
                ratio = max(va, vb) / min(va, vb)
                if ratio > 100:
                    conflicts.append(Contradiction(
                        span_a=sa, span_b=sb,
                        reason=f'numeric conflict: {va} vs {vb} {unit_a} (ratio {ratio:.0f}x)',
                    ))

    # Resolution: keep first of each conflicting pair, append a caveat
    resolved = text
    if conflicts:
        caveat = ' [Note: sources contain conflicting information on this point; verify independently.]'
        resolved = text.rstrip() + caveat

    penalty = min(len(conflicts) * 0.1, 0.4)

    return ContradictionReport(
        contradictions=conflicts,
        resolved_text=resolved,
        has_conflict=bool(conflicts),
        confidence_penalty=round(penalty, 3),
    )

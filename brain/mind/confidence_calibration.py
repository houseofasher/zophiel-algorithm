"""
Confidence Calibration — Produces a calibrated confidence score.
Aggregates signals: RAG hit quality, logic verdict, contradiction penalty,
query clarity, and domain specificity into a single [0,1] score with a
human-readable uncertainty label.
"""
from __future__ import annotations
from dataclasses import dataclass

_LABELS = [
    (0.85, 'high confidence'),
    (0.65, 'moderate confidence'),
    (0.40, 'low confidence'),
    (0.00, 'speculative'),
]

@dataclass
class CalibrationResult:
    score: float          # 0-1
    label: str            # human label
    factors: dict         # breakdown of contributing signals
    should_hedge: bool    # True → prepend hedge phrase to answer

def calibrate(
    rag_score: float = 0.5,
    logic_strength: float = 0.5,
    contradiction_penalty: float = 0.0,
    query_clarity: float = 0.5,
    has_web_source: bool = False,
    domain_match: bool = True,
) -> CalibrationResult:
    """
    Weighted combination of input signals → calibrated confidence.
    """
    weights = {
        'rag_score':             0.30,
        'logic_strength':        0.25,
        'query_clarity':         0.20,
        'domain_match':          0.15,
        'web_source_bonus':      0.10,
    }
    raw = (
        rag_score              * weights['rag_score'] +
        logic_strength         * weights['logic_strength'] +
        query_clarity          * weights['query_clarity'] +
        (1.0 if domain_match else 0.3) * weights['domain_match'] +
        (1.0 if has_web_source else 0.0) * weights['web_source_bonus']
    )
    score = max(0.0, min(1.0, raw - contradiction_penalty))

    label = 'speculative'
    for threshold, lbl in _LABELS:
        if score >= threshold:
            label = lbl
            break

    return CalibrationResult(
        score=round(score, 3),
        label=label,
        factors={
            'rag_score': rag_score,
            'logic_strength': logic_strength,
            'contradiction_penalty': contradiction_penalty,
            'query_clarity': query_clarity,
            'has_web_source': has_web_source,
            'domain_match': domain_match,
        },
        should_hedge=(score < 0.45),
    )

def hedge_phrase(label: str) -> str:
    return {
        'speculative':        'This is speculative, but: ',
        'low confidence':     'Based on available information: ',
        'moderate confidence':'',
        'high confidence':    '',
    }.get(label, '')

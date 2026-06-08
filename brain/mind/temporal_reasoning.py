"""
Temporal Reasoning — Understands time references in queries and answers.
Handles: relative dates, historical periods, sequences, durations, and
flags time-sensitive claims that may be outdated.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import datetime

_NOW = datetime.utcnow()

_RELATIVE = {
    'today':       0,
    'yesterday':   -1,
    'tomorrow':    1,
    'last year':   -365,
    'next year':   365,
    'last week':   -7,
    'next week':   7,
    'last month':  -30,
    'next month':  30,
}

_ERA_MAP = {
    'ancient':     (-3000, 500),
    'medieval':    (500, 1500),
    'renaissance': (1300, 1600),
    'modern':      (1800, 1950),
    'contemporary':(1950, 2100),
    'prehistoric': (-100000, -3000),
}

_STALE_TRIGGERS = re.compile(
    r'\b(current|latest|recent|now|today|this year|at present|currently|'
    r'as of \d{4}|new|modern|up-to-date)\b', re.I,
)

_YEAR_RE = re.compile(r'\b(1\d{3}|20[0-2]\d)\b')
_DURATION_RE = re.compile(r'(\d+\.?\d*)\s*(year|month|week|day|hour|minute|second)s?', re.I)

@dataclass
class TemporalContext:
    years_mentioned: list[int]
    era: str                       # 'ancient', 'modern', etc. or ''
    is_time_sensitive: bool        # likely to be outdated quickly
    sequence_detected: bool        # query asks about order/sequence
    duration_seconds: float        # total duration if parseable, else 0
    temporal_note: str             # advisory note for the answer

def analyse_time(text: str) -> TemporalContext:
    text_low = text.lower()

    # Years
    years = [int(m.group(1)) for m in _YEAR_RE.finditer(text)]

    # Era
    era = ''
    for name, (start, end) in _ERA_MAP.items():
        if name in text_low:
            era = name
            break
    if not era and years:
        y = years[0]
        for name, (start, end) in _ERA_MAP.items():
            if start <= y < end:
                era = name
                break

    # Time sensitivity
    sensitive = bool(_STALE_TRIGGERS.search(text))

    # Sequence
    seq = bool(re.search(r'\b(before|after|first|then|next|finally|step \d|chronolog|sequence|order)\b', text_low))

    # Duration
    total_secs = 0.0
    unit_secs = {
        'year': 365.25 * 86400, 'month': 30.44 * 86400,
        'week': 7 * 86400, 'day': 86400,
        'hour': 3600, 'minute': 60, 'second': 1,
    }
    for m in _DURATION_RE.finditer(text):
        qty = float(m.group(1))
        unit = m.group(2).lower().rstrip('s')
        total_secs += qty * unit_secs.get(unit, 0)

    # Advisory note
    note = ''
    if sensitive:
        note = (f"This answer may contain time-sensitive information. "
                f"Knowledge is current as of approximately {_NOW.year}; verify for the latest data.")
    elif years:
        if max(years) < 1990:
            note = f"This appears to relate to a historical period ({min(years)}–{max(years)})."

    return TemporalContext(
        years_mentioned=years,
        era=era,
        is_time_sensitive=sensitive,
        sequence_detected=seq,
        duration_seconds=round(total_secs, 1),
        temporal_note=note,
    )

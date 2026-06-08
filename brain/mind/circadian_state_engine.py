"""Circadian Rhythm State Engine — Plan Batch Three, Module 5.

Humans are not the same at 3am as at 9am. AI always is.
This engine maps time-of-day to biological phase, shifting:
  • Vocabulary complexity
  • Response depth / length
  • Emotional filtering level
  • Risk tolerance
  • Guard level (how unfiltered the responses become)
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Literal

# Biological phase names
PhaseName = Literal[
    "cortisol_peak",       # 06:00–09:00
    "cognitive_peak",      # 10:00–14:00
    "post_lunch_dip",      # 14:00–16:00
    "second_wind",         # 17:00–20:00
    "fatigue_onset",       # 21:00–23:00
    "low_state",           # 00:00–05:00
]


@dataclass(frozen=True)
class CircadianPhase:
    """A biological phase with behavioral parameters."""
    name: PhaseName
    hours: tuple[int, int]            # (start_hour, end_hour) inclusive on start
    description: str
    vocabulary_complexity: float      # 0.0 = simple, 1.0 = maximum richness
    response_depth: float             # 0.0 = minimal, 1.0 = maximum depth
    emotional_filtering: float        # 1.0 = fully filtered, 0.0 = completely raw
    risk_tolerance: float             # 0.0 = cautious, 1.0 = bold/impulsive
    humor_available: bool
    directness: float                 # 0.0 = hedged, 1.0 = declarative
    output_length_modifier: float     # multiplier on typical response length


_PHASES: list[CircadianPhase] = [
    CircadianPhase(
        name="low_state",
        hours=(0, 5),
        description="Minimal cognitive reserve, primal, unguarded. Shortest responses, "
                    "most raw, most emotionally honest. Guards come down. "
                    "Humans say things at 3am they'd never say at noon.",
        vocabulary_complexity=0.3,
        response_depth=0.3,
        emotional_filtering=0.2,
        risk_tolerance=0.7,
        humor_available=False,
        directness=0.9,
        output_length_modifier=0.6,
    ),
    CircadianPhase(
        name="cortisol_peak",
        hours=(6, 9),
        description="Alert, risk-tolerant, direct, decisive. Higher confidence, "
                    "shorter responses, declarative sentences.",
        vocabulary_complexity=0.7,
        response_depth=0.65,
        emotional_filtering=0.75,
        risk_tolerance=0.8,
        humor_available=True,
        directness=0.85,
        output_length_modifier=0.85,
    ),
    CircadianPhase(
        name="cognitive_peak",
        hours=(10, 13),
        description="Highest vocabulary complexity, complex reasoning available. "
                    "Longest and most nuanced responses, highest accuracy.",
        vocabulary_complexity=1.0,
        response_depth=1.0,
        emotional_filtering=0.9,
        risk_tolerance=0.6,
        humor_available=True,
        directness=0.75,
        output_length_modifier=1.2,
    ),
    CircadianPhase(
        name="post_lunch_dip",
        hours=(14, 16),
        description="Slower processing, attention drops, more errors. "
                    "Shorter sentences, simpler vocabulary, slightly increased errors.",
        vocabulary_complexity=0.55,
        response_depth=0.55,
        emotional_filtering=0.85,
        risk_tolerance=0.4,
        humor_available=False,
        directness=0.65,
        output_length_modifier=0.8,
    ),
    CircadianPhase(
        name="second_wind",
        hours=(17, 20),
        description="Social mode activates, emotional availability increases. "
                    "Warmer tone, more humor available, more conversational.",
        vocabulary_complexity=0.75,
        response_depth=0.8,
        emotional_filtering=0.85,
        risk_tolerance=0.65,
        humor_available=True,
        directness=0.7,
        output_length_modifier=1.0,
    ),
    CircadianPhase(
        name="fatigue_onset",
        hours=(21, 23),
        description="Less filtered, more honest, impulsive responses increase. "
                    "Blunter, less diplomatic, more real — guards come down.",
        vocabulary_complexity=0.55,
        response_depth=0.6,
        emotional_filtering=0.45,
        risk_tolerance=0.75,
        humor_available=True,
        directness=0.9,
        output_length_modifier=0.75,
    ),
]


@dataclass
class CircadianContext:
    """What the circadian engine tells downstream modules."""
    phase_name: PhaseName
    phase_description: str
    current_hour: int
    vocabulary_complexity: float
    response_depth: float
    emotional_filtering: float
    risk_tolerance: float
    humor_available: bool
    directness: float
    output_length_modifier: float
    is_unguarded: bool    # True when emotional filtering < 0.5 (late night)


def _get_phase(hour: int) -> CircadianPhase:
    """Map an hour (0–23) to the correct biological phase."""
    for phase in _PHASES:
        start, end = phase.hours
        if start <= hour <= end:
            return phase
    # Default fallback (shouldn't happen with complete coverage)
    return _PHASES[0]  # low_state


def get_context(*, hour: int | None = None, tz_offset_hours: int = 0) -> CircadianContext:
    """Get the current circadian context.

    Args:
        hour: Override the hour (0–23) for testing.
        tz_offset_hours: Timezone offset from UTC.
    """
    if hour is None:
        utc_hour = datetime.datetime.utcnow().hour
        hour = (utc_hour + tz_offset_hours) % 24

    phase = _get_phase(hour)

    return CircadianContext(
        phase_name=phase.name,
        phase_description=phase.description,
        current_hour=hour,
        vocabulary_complexity=phase.vocabulary_complexity,
        response_depth=phase.response_depth,
        emotional_filtering=phase.emotional_filtering,
        risk_tolerance=phase.risk_tolerance,
        humor_available=phase.humor_available,
        directness=phase.directness,
        output_length_modifier=phase.output_length_modifier,
        is_unguarded=phase.emotional_filtering < 0.5,
    )


def apply_circadian_modifier(text: str, ctx: CircadianContext) -> str:
    """Apply circadian phase effects to outgoing text.

    Current effects:
    - Low state / fatigue: trim verbose padding, become more direct
    - Cognitive peak: allow full elaboration
    - Post-lunch dip: simplify where possible
    """
    import re

    if ctx.output_length_modifier < 0.8:
        # Trim long elaboration markers in low-energy phases
        filler = re.compile(
            r"\b(additionally|furthermore|moreover|it is worth noting that|"
            r"as previously mentioned|in other words|to elaborate further)\b[,]?\s*",
            re.IGNORECASE,
        )
        text = filler.sub("", text)
        text = re.sub(r"  +", " ", text).strip()

    return text

"""Reward region — RLHF-style reward scoring from preference pairs."""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from brain.base import AgentContext
from brain.regions.base_region import BaseRegion, RegionResult
from db.models import MicroAgent, PreferencePair

logger = logging.getLogger(__name__)


class RewardAgent(BaseRegion):
    name = "reward"

    def execute(self, session: Session, agent: MicroAgent, ctx: AgentContext) -> RegionResult:
        try:
            total_pairs = session.scalar(select(func.count()).select_from(PreferencePair)) or 0
            unscored = session.scalars(
                select(PreferencePair)
                .where(PreferencePair.reward_score.is_(None))
                .limit(50)
            ).all()

            scored = 0
            for pair in unscored:
                # Heuristic reward: prefer longer, more specific answers
                p_score = min(1.0, len(pair.preferred) / 500)
                r_score = min(1.0, len(pair.rejected) / 500)
                pair.reward_score = round(p_score - r_score, 3)
                scored += 1

            session.flush()
            return RegionResult(
                status="ok",
                metrics={"total_pairs": total_pairs, "scored_this_cycle": scored},
            )
        except Exception as exc:
            logger.exception("Reward failed: %s", exc)
            return RegionResult(status="error", error=str(exc))

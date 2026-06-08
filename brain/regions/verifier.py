"""Verifier region — quality-score and verify collected documents."""

from __future__ import annotations

import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from brain.base import AgentContext
from brain.regions.base_region import BaseRegion, RegionResult
from db.models import Document, MicroAgent

logger = logging.getLogger(__name__)

_JUNK_PATTERNS = re.compile(
    r"(cookie policy|sign up|log in|subscribe now|404 not found|javascript required)",
    re.I,
)


def _quality_score(text: str) -> float:
    if len(text) < 50:
        return 0.0
    if _JUNK_PATTERNS.search(text):
        return 0.2
    # Basic heuristics: longer, fewer caps-heavy words = higher quality
    words = text.split()
    all_caps = sum(1 for w in words if w.isupper() and len(w) > 2)
    score = min(1.0, len(words) / 200) * (1.0 - min(0.5, all_caps / max(1, len(words))))
    return round(max(0.1, score), 3)


class VerifierAgent(BaseRegion):
    name = "verifier"

    def execute(self, session: Session, agent: MicroAgent, ctx: AgentContext) -> RegionResult:
        try:
            docs = session.scalars(
                select(Document).where(
                    Document.micro_subdomain_id == ctx.micro_subdomain_id,
                    Document.verified == False,  # noqa: E712
                )
            ).all()

            verified = 0
            flagged = 0
            for doc in docs:
                score = _quality_score(doc.text)
                doc.quality_score = score
                doc.verified = True
                if score >= 0.3:
                    verified += 1
                else:
                    flagged += 1

            session.flush()
            return RegionResult(
                status="ok",
                metrics={"verified": verified, "flagged_low_quality": flagged},
            )
        except Exception as exc:
            logger.exception("Verifier failed: %s", exc)
            return RegionResult(status="error", error=str(exc))

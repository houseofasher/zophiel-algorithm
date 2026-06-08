"""Labeler region — teacher model assigns labels to verified documents."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from brain.base import AgentContext
from brain.regions.base_region import BaseRegion, RegionResult
from db.models import Document, DocumentLabel, MicroAgent

logger = logging.getLogger(__name__)


def _teacher_label(text: str, micro_slug: str) -> tuple[str, float]:
    """Simple keyword-based teacher label. Returns (label, confidence)."""
    text_lower = text.lower()
    topic = micro_slug.replace("_", " ")
    if topic in text_lower:
        return micro_slug, 0.9
    # Keyword match heuristic
    words = set(text_lower.split())
    topic_words = set(micro_slug.split("_"))
    overlap = len(words & topic_words)
    if overlap >= 2:
        return micro_slug, 0.75
    if overlap == 1:
        return micro_slug, 0.6
    return "general", 0.5


class LabelerAgent(BaseRegion):
    name = "labeler"

    def execute(self, session: Session, agent: MicroAgent, ctx: AgentContext) -> RegionResult:
        try:
            docs = session.scalars(
                select(Document).where(
                    Document.micro_subdomain_id == ctx.micro_subdomain_id,
                    Document.verified == True,  # noqa: E712
                    Document.quality_score >= 0.3,
                )
            ).all()

            labeled = 0
            flagged_review = 0
            for doc in docs:
                existing = session.query(DocumentLabel).filter_by(document_id=doc.id).first()
                if existing:
                    continue
                label, confidence = _teacher_label(doc.text, ctx.micro_subdomain_slug)
                needs_review = confidence < 0.65
                dl = DocumentLabel(
                    document_id=doc.id,
                    label=label,
                    confidence=confidence,
                    review_flag=needs_review,
                )
                session.add(dl)
                labeled += 1
                if needs_review:
                    flagged_review += 1

            session.flush()
            return RegionResult(
                status="ok",
                metrics={"labeled": labeled, "flagged_for_review": flagged_review},
            )
        except Exception as exc:
            logger.exception("Labeler failed: %s", exc)
            return RegionResult(status="error", error=str(exc))

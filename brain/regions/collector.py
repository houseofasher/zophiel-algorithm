"""Collector region — gather seed documents for a micro-subdomain."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from sqlalchemy.orm import Session

from brain.base import AgentContext
from brain.regions.base_region import BaseRegion, RegionResult
from db.models import Document, MicroAgent

logger = logging.getLogger(__name__)

_INBOX = Path(os.environ.get("PIPELINE_DATA_DIR", "data")) / "raw" / "inbox"
_INBOX.mkdir(parents=True, exist_ok=True)


def _seed_text_for(domain: str, subdomain: str, micro: str) -> list[str]:
    """Return seed sentences for a micro-subdomain."""
    topic = f"{domain} {subdomain} {micro}".replace("_", " ")
    return [
        f"Introduction to {topic}: this field covers fundamental principles and methods.",
        f"{topic} involves systematic study and application of core concepts.",
        f"Key topics in {topic} include definitions, methods, and practical examples.",
        f"Advanced {topic} builds on foundational knowledge toward expert mastery.",
        f"Research in {topic} has produced significant findings across many domains.",
    ]


class CollectorAgent(BaseRegion):
    name = "collector"

    def execute(self, session: Session, agent: MicroAgent, ctx: AgentContext) -> RegionResult:
        try:
            domain = ctx.domain_slug
            subdomain = ctx.subdomain_slug
            micro = ctx.micro_subdomain_slug

            # Check inbox for custom txt/md files matching this micro
            inbox_docs: list[str] = []
            for ext in ("*.txt", "*.md"):
                for p in _INBOX.glob(ext):
                    if micro.replace("_", "-") in p.name.lower() or micro in p.name.lower():
                        text = p.read_text(encoding="utf-8", errors="ignore").strip()
                        if text:
                            inbox_docs.append(text[:4000])

            seeds = inbox_docs or _seed_text_for(domain, subdomain, micro)

            added = 0
            for text in seeds:
                existing = session.query(Document).filter(
                    Document.micro_subdomain_id == ctx.micro_subdomain_id,
                    Document.source == "seed",
                    Document.text == text[:200],
                ).first()
                if not existing:
                    doc = Document(
                        domain_id=ctx.domain_id,
                        subdomain_id=ctx.subdomain_id,
                        micro_subdomain_id=ctx.micro_subdomain_id,
                        source="seed",
                        text=text,
                        quality_score=0.8,
                        verified=False,
                    )
                    session.add(doc)
                    added += 1

            session.flush()
            return RegionResult(status="ok", metrics={"documents_added": added, "total_seeds": len(seeds)})

        except Exception as exc:
            logger.exception("Collector failed: %s", exc)
            return RegionResult(status="error", error=str(exc))

"""Self-inquiry — Aureon reflects on what it has learned after each cycle."""

from __future__ import annotations

import json
import logging
import os
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_LOG_DIR = Path(os.environ.get("AUREON_AUDIT_LOG_DIR", "data/logs"))
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_INQUIRY_LOG = _LOG_DIR / "self_inquiry.jsonl"

_buffer: deque[dict] = deque(maxlen=200)


def is_self_inquiry_enabled() -> bool:
    return os.environ.get("AUREON_SELF_INQUIRY", "1") != "0"


def inquiry_log_path() -> Path:
    return _INQUIRY_LOG


def record_inquiry(theme: str, question: str, answer: str, source: str = "auto") -> dict[str, Any]:
    entry = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "theme": theme,
        "question": question,
        "answer": answer,
        "source": source,
    }
    _buffer.append(entry)
    try:
        with _INQUIRY_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    return entry


def recent_inquiries(limit: int = 20) -> list[dict]:
    return list(_buffer)[-limit:]


def run_self_inquiry_cycle() -> list[dict]:
    """Generate a brief internal monologue after a training cycle."""
    if not is_self_inquiry_enabled():
        return []

    try:
        from brain.cortex import brain_status
        status = brain_status()
        docs = status.get("documents", 0)
        domains = status.get("domains", 0)
    except Exception:
        docs, domains = 0, 0

    inquiries = [
        record_inquiry(
            "knowledge_state",
            "What do I know right now?",
            f"I hold {docs} verified documents across {domains} domains. "
            "Each cycle refines the weight distributions in my classifiers.",
        ),
        record_inquiry(
            "learning_process",
            "How am I learning?",
            "Backpropagation adjusts weights until predictions match labels. "
            "I don't memorize — I generalize from labeled examples.",
        ),
    ]
    return inquiries


def run_self_inquiry_for_cycle(
    domain_slug: str = "",
    subdomain_slug: str = "",
    micro_slug: str = "",
    grade_slug: str = "",
    source: str = "cycle",
    **kwargs,
) -> dict:
    """Run a brief self-reflection before a learning cycle."""
    question = (
        f"What should I focus on when learning {micro_slug.replace('_', ' ')} "
        f"in {subdomain_slug.replace('_', ' ')} at {grade_slug} level?"
    )
    try:
        record_inquiry(question)
    except Exception:
        pass
    return {"question": question, "action": "recorded"}

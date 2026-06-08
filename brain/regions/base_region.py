"""Base class for all brain regions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from brain.base import AgentContext
from db.models import MicroAgent


@dataclass
class RegionResult:
    status: str  # "ok" | "skipped" | "error"
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class BaseRegion:
    name: str = "base"

    def execute(self, session: Session, agent: MicroAgent, ctx: AgentContext) -> RegionResult:
        raise NotImplementedError

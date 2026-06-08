"""Evaluator region — benchmark accuracy + halt on regression."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from brain.base import AgentContext
from brain.regions.base_region import BaseRegion, RegionResult
from db.models import BenchmarkResult, MicroAgent, TrainingRun

logger = logging.getLogger(__name__)

_MIN_ACCURACY_BY_GRADE = {
    "preschool": 0.40,
    "elementary": 0.50,
    "middle_school": 0.60,
    "high_school": 0.65,
    "undergraduate": 0.70,
    "masters": 0.75,
    "doctorate": 0.80,
}


class EvaluatorAgent(BaseRegion):
    name = "evaluator"

    def execute(self, session: Session, agent: MicroAgent, ctx: AgentContext) -> RegionResult:
        try:
            grade = ctx.grade_slug or "preschool"
            threshold = _MIN_ACCURACY_BY_GRADE.get(grade, 0.5)

            latest_run = session.scalars(
                select(TrainingRun)
                .where(
                    TrainingRun.micro_subdomain_slug == ctx.micro_subdomain_slug,
                    TrainingRun.grade_slug == grade,
                )
                .order_by(TrainingRun.created_at.desc())
                .limit(1)
            ).first()

            if not latest_run:
                return RegionResult(status="skipped", metrics={"reason": "no_training_run"})

            accuracy = latest_run.accuracy or 0.0
            passed = accuracy >= threshold

            result = BenchmarkResult(
                run_id=latest_run.run_id,
                benchmark_name=f"grade_{grade}_accuracy",
                score=accuracy,
                details={"threshold": threshold, "passed": passed, "grade": grade},
            )
            session.add(result)
            session.flush()

            return RegionResult(
                status="ok",
                metrics={
                    "accuracy": accuracy,
                    "threshold": threshold,
                    "passed": passed,
                    "grade": grade,
                },
            )
        except Exception as exc:
            logger.exception("Evaluator failed: %s", exc)
            return RegionResult(status="error", error=str(exc))

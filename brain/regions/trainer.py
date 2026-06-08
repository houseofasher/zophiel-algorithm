"""Trainer region — backpropagation classifier per micro-subdomain + grade."""

from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from brain.base import AgentContext
from brain.regions.base_region import BaseRegion, RegionResult
from db.models import Document, DocumentLabel, MicroAgent, TrainingRun
from src.neural_network import NeuralNetwork
from src.text_features import TextFeatureExtractor

logger = logging.getLogger(__name__)

MODELS_DIR = Path(os.environ.get("PIPELINE_DATA_DIR", "data")) / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def _get_labeled_docs(session: Session, micro_id: int) -> tuple[list[str], list[str]]:
    rows = session.execute(
        select(Document.text, DocumentLabel.label)
        .join(DocumentLabel, DocumentLabel.document_id == Document.id)
        .where(Document.micro_subdomain_id == micro_id, Document.quality_score >= 0.3)
    ).all()
    texts = [r[0] for r in rows]
    labels = [r[1] for r in rows]
    return texts, labels


class TrainerAgent(BaseRegion):
    name = "trainer"

    def execute(self, session: Session, agent: MicroAgent, ctx: AgentContext) -> RegionResult:
        try:
            texts, labels = _get_labeled_docs(session, ctx.micro_subdomain_id)

            if len(texts) < 2:
                return RegionResult(
                    status="skipped",
                    metrics={"reason": "insufficient_data", "docs": len(texts)},
                )

            unique_labels = sorted(set(labels))
            if len(unique_labels) < 2:
                # Pad with a dummy negative class
                texts.append("irrelevant document about unrelated topic")
                labels.append("other")
                unique_labels = sorted(set(labels))

            label_idx = {l: i for i, l in enumerate(unique_labels)}
            y = np.array([label_idx[l] for l in labels], dtype=np.int64)

            extractor = TextFeatureExtractor(max_features=256)
            X = extractor.fit_transform(texts)

            if X.shape[1] == 0:
                return RegionResult(status="skipped", metrics={"reason": "no_features"})

            n_classes = len(unique_labels)
            epochs = ctx.epochs if ctx.epochs else 150

            network = NeuralNetwork(
                layer_sizes=[X.shape[1], min(128, X.shape[1] * 2), n_classes],
                learning_rate=0.05,
                seed=42,
                output_activation="softmax",
            )
            network.train(X, y, epochs=epochs, verbose_every=0)
            metrics = network.evaluate(X, y)

            # Save artifact
            run_id = str(uuid.uuid4())[:12]
            scope = f"{ctx.domain_slug}.{ctx.subdomain_slug}.{ctx.micro_subdomain_slug}"
            artifact_dir = MODELS_DIR / run_id
            artifact_dir.mkdir(parents=True, exist_ok=True)
            artifact_path = artifact_dir / "model.json"
            network.save(artifact_path)
            meta = {
                "scope": scope,
                "labels": unique_labels,
                "feature_extractor": extractor.to_dict(),
                "grade": ctx.grade_slug,
                "accuracy": metrics["accuracy"],
            }
            (artifact_dir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")

            # Persist training run
            promoted = metrics["accuracy"] >= 0.6
            run = TrainingRun(
                run_id=run_id,
                domain_slug=ctx.domain_slug,
                subdomain_slug=ctx.subdomain_slug,
                micro_subdomain_slug=ctx.micro_subdomain_slug,
                grade_slug=ctx.grade_slug,
                accuracy=metrics["accuracy"],
                loss=metrics["loss"],
                epochs=epochs,
                promoted=promoted,
                artifact_path=str(artifact_path),
                metrics=metrics,
            )
            session.add(run)
            session.flush()

            return RegionResult(
                status="ok",
                metrics={
                    **metrics,
                    "docs": len(texts),
                    "classes": n_classes,
                    "run_id": run_id,
                    "promoted": promoted,
                },
            )

        except Exception as exc:
            logger.exception("Trainer failed: %s", exc)
            return RegionResult(status="error", error=str(exc))

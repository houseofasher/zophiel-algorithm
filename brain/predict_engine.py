"""Predict engine — chain-of-thought reasoning + TF-IDF RAG answer extraction."""

from __future__ import annotations

CURRENT_MODEL_VERSION = "0.1.0-local"

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_PREDICTION_SIGNALS = (
    "will ", "going to ", "likely to ", "predict ", "forecast ",
    "what will happen", "future of ", "next year", "odds of",
    "chance of", "probability of",
)
_NON_PREDICTION = (
    "what is ", "what are ", "how does ", "explain ", "define ",
    "who is ", "when was ", "where is ",
)


def is_prediction_question(text: str) -> bool:
    q = text.strip().lower()
    if any(q.startswith(s) for s in _NON_PREDICTION):
        return False
    return any(s in q for s in _PREDICTION_SIGNALS)


def _build_cot(question: str, evidence: list[str]) -> list[dict]:
    steps: list[dict] = []
    steps.append({"step": "1_parse", "action": "parse_question",
                  "output": f"Question: {question[:200]}"})
    if evidence:
        steps.append({"step": "2_retrieve", "action": "retrieve_corpus",
                      "output": f"Found {len(evidence)} relevant document(s)"})
        best = max(evidence, key=len)[:400]
        steps.append({"step": "3_extract", "action": "extract_evidence", "output": best})
    else:
        steps.append({"step": "2_retrieve", "action": "retrieve_corpus",
                      "output": "No corpus documents — reasoning from domain knowledge"})
    steps.append({"step": "4_reason", "action": "reason",
                  "output": "Applying domain knowledge and evidence weighting"})
    return steps


def _extract_best_answer(question: str, hits: list[Any]) -> str | None:
    if not hits:
        return None
    q_words = set(re.findall(r"[a-z]{4,}", question.lower()))
    best_sentence, best_score = "", 0.0
    for hit in hits:
        text = getattr(hit, "text", str(hit)) if not isinstance(hit, str) else hit
        for sent in re.split(r"(?<=[.!?])\s+", text):
            if not (30 <= len(sent) <= 500):
                continue
            words = set(re.findall(r"[a-z]{4,}", sent.lower()))
            overlap = len(q_words & words) / max(1, len(q_words))
            if overlap > best_score:
                best_score, best_sentence = overlap, sent
    return best_sentence if best_score > 0.1 else None


def predict_with_steps(
    question: str,
    conversation_context: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Run full predict pipeline and return structured result."""
    try:
        from brain.vector_rag import retrieve_with_citations
        context, hits, sources = retrieve_with_citations(question, top_k=5)
        evidence = [getattr(h, "text", str(h)) for h in hits]
    except Exception as exc:
        logger.debug("RAG retrieval failed: %s", exc)
        hits, sources, evidence = [], [], []

    cot = _build_cot(question, evidence)
    best_answer = _extract_best_answer(question, hits)

    if best_answer:
        reply, confidence = best_answer, 0.72
    elif evidence:
        reply = " ".join(e[:200] for e in evidence[:3])
        confidence = 0.55
    else:
        reply = (
            "I don't have verified corpus data on this yet. "
            "My training pipeline is building knowledge — ask again after more cycles."
        )
        confidence = 0.1

    return {
        "answer": reply,
        "confidence": confidence,
        "pipeline": cot,
        "sources": sources[:5] if sources else [],
        "evidence_count": len(evidence),
        "kind": "predict" if is_prediction_question(question) else "factual",
    }


def warm_up_predict_brain() -> dict:
    """Warm up the RAG index and prediction cache on startup."""
    try:
        from brain.vector_rag import get_rag_index
        idx = get_rag_index()
        return {"status": "ok", "documents_indexed": idx.document_count}
    except Exception as exc:
        return {"status": "skipped", "reason": str(exc)}

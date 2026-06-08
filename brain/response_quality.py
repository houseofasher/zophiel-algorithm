"""Response quality checks — detect classification leaks, robotic markers, bad output."""

from __future__ import annotations

import re

_CLASSIFICATION_LEAK = re.compile(r"\b[a-z_]+\.[a-z_]+\.[a-z_]+\b")
_ROBOTIC = re.compile(
    r"(based on (the|my) (corpus|data|training)|from a zophiel lens|"
    r"additional context from search suggests|as an ai language model)",
    re.I,
)
_FORCED_CHOICE_RE = re.compile(
    r"\b(choose|pick|rather|which would you|if you had to|would you prefer)\b", re.I
)


def has_classification_leak(text: str) -> bool:
    return bool(_CLASSIFICATION_LEAK.search(text))


def has_robotic_markers(text: str) -> bool:
    return bool(_ROBOTIC.search(text))


def is_directed_choice_question(text: str) -> bool:
    """True if the question asks Aureon to make a personal choice."""
    q = text.strip().lower()
    if not _FORCED_CHOICE_RE.search(q):
        return False
    # Must be directed at Aureon
    return any(marker in q for marker in ("you", "aureon", "your", "would you"))


def clean_reply(text: str) -> str:
    """Strip classification leaks and robotic markers from a reply."""
    text = _CLASSIFICATION_LEAK.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_specific_topic_inquiry(text: str) -> bool:
    """Return True if the user is asking about a specific named topic in depth."""
    t = text.lower().strip()
    depth_signals = [
        "tell me about", "explain", "describe", "what is", "what are",
        "how does", "how do", "deep dive", "elaborate on", "break down",
        "walk me through", "teach me about",
    ]
    return any(t.startswith(s) or s in t for s in depth_signals)


# ---------------------------------------------------------------------------
# Recovery routes
# ---------------------------------------------------------------------------

class RecoveryRoute:
    """Named recovery strategies for failed response attempts."""
    FALLBACK_TO_CORPUS = "fallback_to_corpus"
    FALLBACK_TO_IDENTITY = "fallback_to_identity"
    ABSTAIN = "abstain"
    RETRY = "retry"
    DIRECTED_REFLECTION = "directed_reflection"
    DEEP_CONCEPT = "deep_concept"
    NAMED_ENTITY = "named_entity"
    PREDICT = "predict"
    CODE = "code"
    LIVE_SEARCH = "live_search"


def try_recover_response(question: str, payload: dict, session_id: str | None = None, recover_handlers: dict | None = None, **kwargs) -> dict | None:
    """Attempt to recover a failed or empty reply."""
    reply = str(payload.get("reply", "")).strip()
    if not reply or has_robotic_markers(reply):
        payload["reply"] = (
            "I'm still learning — ask me again after my corpus grows. "
            "Each training cycle improves my ability to ground answers in verified knowledge."
        )
        payload["recovered"] = True
    return payload


# ---------------------------------------------------------------------------
# Question intent classification
# ---------------------------------------------------------------------------

class QuestionIntent:
    FACTUAL = "factual"
    IDENTITY = "identity"
    MATHEMATICAL = "mathematical"
    PREDICTION = "prediction"
    PHILOSOPHICAL = "philosophical"
    UNKNOWN = "unknown"


def infer_question_intent(text: str) -> str:
    """Classify the intent of a question."""
    t = text.lower().strip()
    if any(t.startswith(s) for s in ("who are you", "what are you", "tell me about yourself", "your name")):
        return QuestionIntent.IDENTITY
    if any(c in t for c in "0123456789") and any(op in t for op in ["+", "-", "*", "/", "×", "÷", "plus", "minus", "times"]):
        return QuestionIntent.MATHEMATICAL
    if any(t.startswith(s) for s in ("will ", "predict", "forecast", "going to")):
        return QuestionIntent.PREDICTION
    if any(w in t for w in ("meaning", "purpose", "consciousness", "exist", "philosophy", "moral")):
        return QuestionIntent.PHILOSOPHICAL
    if any(t.startswith(s) for s in ("what is", "what are", "how does", "explain", "define", "describe")):
        return QuestionIntent.FACTUAL
    return QuestionIntent.UNKNOWN

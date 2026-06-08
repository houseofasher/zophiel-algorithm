"""
LEARNER — Module 11 of the Zophiel Mind
Fast learning from new information. Updates working knowledge within a session,
flags contradictions with existing knowledge, and stores high-value facts.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LearningEvent:
    fact: str
    source: str
    confidence: float
    domain: str
    timestamp: float
    contradiction: str | None = None  # existing belief this contradicts


@dataclass
class LearnerState:
    session_facts: list[LearningEvent] = field(default_factory=list)
    contradictions: list[tuple[str,str]] = field(default_factory=list)
    domains_touched: set[str] = field(default_factory=set)


_FACT_RE = re.compile(
    r'(?:(?:is|are|was|were)\s+(?:a|an|the|known as)?\s*(.{5,80}?)(?:[.,;]|$))',
    re.I
)
_DEFINITION_RE = re.compile(r'(.{3,40}?)\s+(?:means?|refers? to|is defined as|denotes?)\s+(.{5,100}?)(?:[.,;]|$)', re.I)


class Learner:
    """
    Absorbs new information as it arrives.
    Maintains a session-level working memory of acquired facts.
    Flags when new information contradicts previously learned facts.
    Can optionally persist learning to disk.
    """

    def __init__(self, persist_path: str | None = None):
        self.state  = LearnerState()
        self._persist = persist_path
        self._cache: dict[str, str] = {}   # fact_hash → fact text

        if persist_path and Path(persist_path).exists():
            self._load(persist_path)

    def absorb(self, text: str, source: str = "input", domain: str = "general") -> list[LearningEvent]:
        """Extract and store facts from a body of text."""
        facts   = self._extract_facts(text)
        events  = []
        for fact, conf in facts:
            contradiction = self._check_contradiction(fact)
            ev = LearningEvent(
                fact=fact,
                source=source,
                confidence=conf,
                domain=domain,
                timestamp=time.time(),
                contradiction=contradiction,
            )
            self.state.session_facts.append(ev)
            self.state.domains_touched.add(domain)
            if contradiction:
                self.state.contradictions.append((fact, contradiction))
            h = hashlib.md5(fact.lower().encode()).hexdigest()[:8]
            self._cache[h] = fact
            events.append(ev)

        if self._persist:
            self._save(self._persist)

        return events

    def recall(self, query: str, domain: str | None = None) -> list[LearningEvent]:
        """Retrieve relevant facts from session memory."""
        keywords = set(re.findall(r'\b\w{4,}\b', query.lower()))
        results  = []
        for ev in self.state.session_facts:
            fact_words = set(re.findall(r'\b\w{4,}\b', ev.fact.lower()))
            overlap    = keywords & fact_words
            if overlap and (domain is None or ev.domain == domain):
                results.append(ev)
        results.sort(key=lambda e: e.confidence, reverse=True)
        return results[:5]

    def what_do_i_know(self) -> dict[str, Any]:
        return {
            "session_facts": len(self.state.session_facts),
            "contradictions": len(self.state.contradictions),
            "domains": list(self.state.domains_touched),
            "high_confidence": [e.fact for e in self.state.session_facts if e.confidence >= 0.8][:5],
        }

    def _extract_facts(self, text: str) -> list[tuple[str, float]]:
        facts = []
        for m in _DEFINITION_RE.finditer(text):
            facts.append((f"{m.group(1).strip()} means {m.group(2).strip()}", 0.85))
        for m in _FACT_RE.finditer(text):
            candidate = m.group(1).strip()
            if len(candidate.split()) >= 3:
                facts.append((candidate, 0.65))
        # Deduplicate
        seen = set()
        unique = []
        for f, c in facts:
            key = f.lower()[:50]
            if key not in seen:
                seen.add(key)
                unique.append((f, c))
        return unique[:20]

    def _check_contradiction(self, new_fact: str) -> str | None:
        new_words = set(re.findall(r'\b\w{4,}\b', new_fact.lower()))
        for ev in self.state.session_facts:
            old_words = set(re.findall(r'\b\w{4,}\b', ev.fact.lower()))
            overlap   = new_words & old_words
            if len(overlap) >= 3:
                # Check for semantic negation pattern
                negated = re.sub(r'\b(not|never|no|isn\'t|aren\'t|wasn\'t)\b', '', new_fact, flags=re.I)
                if negated.strip() != new_fact.strip():
                    return ev.fact
        return None

    def _save(self, path: str) -> None:
        try:
            data = [
                {"fact": e.fact, "source": e.source, "confidence": e.confidence,
                 "domain": e.domain, "timestamp": e.timestamp}
                for e in self.state.session_facts
            ]
            Path(path).write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load(self, path: str) -> None:
        try:
            data = json.loads(Path(path).read_text())
            for d in data:
                self.state.session_facts.append(LearningEvent(**d))
        except Exception:
            pass


# ── Singleton ─────────────────────────────────────────────────────────────────
_PERSIST = os.environ.get("ZOPHIEL_LEARNER_PATH")
_learner = Learner(persist_path=_PERSIST)

def absorb(text: str, source: str = "input", domain: str = "general") -> list[LearningEvent]:
    return _learner.absorb(text, source, domain)

def recall(query: str, domain: str | None = None) -> list[LearningEvent]:
    return _learner.recall(query, domain)

def what_do_i_know() -> dict:
    return _learner.what_do_i_know()

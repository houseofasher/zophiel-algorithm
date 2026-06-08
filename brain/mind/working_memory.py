"""
Working Memory — Short-term contextual buffer.
Stores the last N turns with key facts extracted, enabling within-session
coherence: pronoun resolution, topic tracking, and context injection.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
import re, time

MAX_TURNS = 12
MAX_FACT_TOKENS = 40

@dataclass
class Turn:
    role: str          # 'user' | 'assistant'
    text: str
    timestamp: float = field(default_factory=time.time)
    key_facts: list[str] = field(default_factory=list)

@dataclass
class WorkingMemoryState:
    turns: list[Turn]
    active_topics: list[str]
    last_subject: str
    context_summary: str

class WorkingMemory:
    def __init__(self, max_turns: int = MAX_TURNS):
        self._turns: deque[Turn] = deque(maxlen=max_turns)

    def push(self, role: str, text: str) -> None:
        facts = self._extract_facts(text)
        self._turns.append(Turn(role=role, text=text, key_facts=facts))

    def _extract_facts(self, text: str) -> list[str]:
        """Pull short noun phrases / named entities as key facts."""
        facts = []
        # Capitalised multi-word phrases
        for m in re.finditer(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})', text):
            facts.append(m.group(1))
        # Numbers with units
        for m in re.finditer(r'\b\d[\d.,]*\s*(?:km|kg|m|°C|eV|GeV|%|years?|days?)\b', text):
            facts.append(m.group(0))
        return facts[:6]

    def get_state(self) -> WorkingMemoryState:
        turns = list(self._turns)
        # Active topics: most frequent nouns across recent turns
        all_facts: list[str] = []
        for t in turns[-6:]:
            all_facts.extend(t.key_facts)
        freq: dict[str, int] = {}
        for f in all_facts:
            freq[f] = freq.get(f, 0) + 1
        active = sorted(freq, key=lambda k: -freq[k])[:5]

        last_subject = ''
        for t in reversed(turns):
            if t.role == 'user' and t.key_facts:
                last_subject = t.key_facts[0]
                break

        summary_parts = [f"{t.role}: {t.text[:60]}" for t in turns[-4:]]
        return WorkingMemoryState(
            turns=turns,
            active_topics=active,
            last_subject=last_subject,
            context_summary=' | '.join(summary_parts),
        )

    def resolve_pronouns(self, text: str) -> str:
        """Replace 'it' / 'that' with the last known subject when unambiguous."""
        state = self.get_state()
        if not state.last_subject:
            return text
        resolved = re.sub(
            r'\b(it|that|this|they|them)\b',
            state.last_subject,
            text,
            count=2,
            flags=re.IGNORECASE,
        )
        return resolved

    def clear(self) -> None:
        self._turns.clear()


_wm = WorkingMemory()

def push(role: str, text: str) -> None:
    _wm.push(role, text)

def get_state() -> WorkingMemoryState:
    return _wm.get_state()

def resolve_pronouns(text: str) -> str:
    return _wm.resolve_pronouns(text)

def clear() -> None:
    _wm.clear()

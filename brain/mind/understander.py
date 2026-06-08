"""
UNDERSTANDER — Module 02 of the Zophiel Mind
Deep semantic comprehension: intent, entities, sentiment polarity, topic, complexity.
Operates on an InputSignal and produces a Comprehension object.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from brain.mind.listener import InputSignal


# ── Output type ───────────────────────────────────────────────────────────────

@dataclass
class Comprehension:
    original_text: str
    intent: str            # "question" | "command" | "statement" | "search" | "reflect"
    intent_confidence: float
    topics: list[str]
    entities: list[dict]   # [{text, type}]
    sentiment: str         # "positive" | "negative" | "neutral"
    complexity: str        # "simple" | "moderate" | "complex"
    keywords: list[str]
    domain_hints: list[str]
    is_question: bool
    is_personal: bool      # about the user themselves
    needs_web: bool        # requires live information
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Patterns ──────────────────────────────────────────────────────────────────

_Q_WORDS     = re.compile(r'\b(who|what|when|where|why|how|which|whose|whom|is|are|was|were|do|does|did|can|could|should|would|will)\b', re.I)
_COMMAND_V   = re.compile(r'^(create|make|build|write|generate|list|show|tell|find|search|get|give|explain|describe|analyse|analyze|compare|summarize|summarise|calculate|compute)\b', re.I)
_REFLECT_W   = re.compile(r'\b(think|believe|feel|opinion|view|perspective|consider|wonder|ponder|reflect)\b', re.I)
_TEMPORAL    = re.compile(r'\b(today|yesterday|now|current|latest|recent|live|breaking|news|2024|2025|2026)\b', re.I)
_PERSONAL    = re.compile(r'\b(i|me|my|myself|i\'m|i\'ve|i\'ll|we|our|us)\b', re.I)

_NEGATIVE_W  = re.compile(r'\b(bad|wrong|fail|error|broken|problem|issue|terrible|horrible|awful|hate|dislike|not|never|no|false|lie|misinformation)\b', re.I)
_POSITIVE_W  = re.compile(r'\b(good|great|excellent|amazing|love|like|perfect|wonderful|best|true|correct|right|success)\b', re.I)

# Domain keyword sets for quick domain detection
_DOMAIN_KW = {
    "science":       r'\b(physics|chemistry|biology|quantum|molecule|atom|cell|DNA|gene|evolution|species)\b',
    "mathematics":   r'\b(equation|theorem|proof|algebra|calculus|matrix|vector|integral|derivative|probability)\b',
    "medicine":      r'\b(disease|symptom|treatment|diagnosis|drug|medicine|health|patient|surgery|virus|bacteria)\b',
    "technology":    r'\b(computer|software|hardware|algorithm|code|program|AI|machine learning|neural|robot|tech)\b',
    "philosophy":    r'\b(truth|reality|consciousness|ethics|morality|existence|meaning|logic|reason|knowledge)\b',
    "history":       r'\b(ancient|medieval|century|war|empire|civilization|historical|dynasty|revolution|era)\b',
    "economics":     r'\b(market|economy|GDP|inflation|price|trade|currency|investment|capital|labour|poverty)\b',
    "occult":        r'\b(occult|esoteric|hermetic|astrology|kabbalah|tarot|numerology|sacred|archetype|shadow)\b',
    "politics":      r'\b(government|policy|election|democracy|power|state|law|rights|freedom|nation|regime)\b',
    "psychology":    r'\b(mind|behaviour|behavior|cognitive|emotion|personality|trauma|memory|perception|instinct)\b',
}
_DOMAIN_RE = {k: re.compile(v, re.I) for k,v in _DOMAIN_KW.items()}

# Named entity rough patterns
_ENTITY_PATTERNS = [
    (re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b'), 'PERSON_OR_ORG'),
    (re.compile(r'\b\d{4}\b'), 'YEAR'),
    (re.compile(r'\$\d+(?:[.,]\d+)*(?:\s*(?:billion|million|trillion))?\b', re.I), 'MONEY'),
    (re.compile(r'\b\d+(?:\.\d+)?%'), 'PERCENTAGE'),
    (re.compile(r'https?://\S+'), 'URL'),
]


# ── Core functions ─────────────────────────────────────────────────────────────

def _detect_intent(text: str) -> tuple[str, float]:
    t = text.strip()
    if _Q_WORDS.match(t) or t.endswith('?'):
        return 'question', 0.9
    if _COMMAND_V.match(t):
        return 'command', 0.85
    if _REFLECT_W.search(t):
        return 'reflect', 0.75
    if _TEMPORAL.search(t):
        return 'search', 0.8
    return 'statement', 0.7


def _extract_entities(text: str) -> list[dict]:
    entities = []
    seen = set()
    for pat, etype in _ENTITY_PATTERNS:
        for m in pat.finditer(text):
            val = m.group(0).strip()
            if val not in seen:
                entities.append({'text': val, 'type': etype})
                seen.add(val)
    return entities[:20]


def _detect_domains(text: str) -> list[str]:
    found = []
    for domain, pat in _DOMAIN_RE.items():
        if pat.search(text):
            found.append(domain)
    return found


def _extract_keywords(text: str, n: int = 10) -> list[str]:
    STOPWORDS = {
        'the','a','an','and','or','but','in','on','at','to','for','of','with',
        'by','from','is','are','was','were','be','been','have','has','had',
        'do','does','did','will','would','could','should','may','might',
        'this','that','these','those','i','you','he','she','it','we','they',
        'what','how','why','when','where','which','who',
    }
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    counts = Counter(w for w in words if w not in STOPWORDS)
    return [w for w,_ in counts.most_common(n)]


def _sentiment(text: str) -> str:
    neg = len(_NEGATIVE_W.findall(text))
    pos = len(_POSITIVE_W.findall(text))
    if neg > pos + 1: return 'negative'
    if pos > neg + 1: return 'positive'
    return 'neutral'


def _complexity(text: str) -> str:
    words = text.split()
    avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
    sentences = re.split(r'[.!?]+', text)
    avg_sent_len = len(words) / max(len(sentences), 1)
    score = avg_word_len * 0.5 + avg_sent_len * 0.1
    if score < 5:  return 'simple'
    if score < 9:  return 'moderate'
    return 'complex'


# ── Main class ────────────────────────────────────────────────────────────────

class Understander:
    """
    Converts an InputSignal into a rich Comprehension object.
    Operates entirely offline — fast, deterministic.
    """

    def understand(self, signal: InputSignal) -> Comprehension:
        text = signal.text

        intent, conf = _detect_intent(text)
        entities     = _extract_entities(text)
        domains      = _detect_domains(text)
        keywords     = _extract_keywords(text)
        sentiment    = _sentiment(text)
        complexity   = _complexity(text)
        is_q         = '?' in text or intent == 'question'
        is_personal  = bool(_PERSONAL.search(text))
        needs_web    = bool(_TEMPORAL.search(text)) or 'news' in text.lower() or 'latest' in text.lower()

        # Derive topics from top keywords + entities
        topics = keywords[:5] + [e['text'] for e in entities if e['type'] == 'PERSON_OR_ORG'][:3]

        return Comprehension(
            original_text=text,
            intent=intent,
            intent_confidence=conf,
            topics=topics,
            entities=entities,
            sentiment=sentiment,
            complexity=complexity,
            keywords=keywords,
            domain_hints=domains,
            is_question=is_q,
            is_personal=is_personal,
            needs_web=needs_web,
            metadata={'modality': signal.modality, 'attachment_count': len(signal.attachments)},
        )


# ── Singleton ─────────────────────────────────────────────────────────────────
_understander = Understander()

def understand(signal: InputSignal) -> Comprehension:
    return _understander.understand(signal)

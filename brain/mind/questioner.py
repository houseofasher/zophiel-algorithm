"""
QUESTIONER — Module 03 of the Zophiel Mind
Socratic questioning engine: asks the precise simple question that unlocks the answer.
The smartest minds ask small questions, not grand ones.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Optional

from brain.mind.understander import Comprehension


@dataclass
class QuestionSet:
    clarifying: list[str]     # questions to sharpen the query
    deepening: list[str]      # questions to go deeper once answered
    socratic: list[str]       # questions that challenge assumptions
    primary: str              # the single best question to ask right now
    should_ask: bool          # True if clarification genuinely needed


# ── Question templates by intent ──────────────────────────────────────────────

_CLARIFY = {
    "question": [
        "What specific aspect of {topic} are you most interested in?",
        "Are you looking for a historical overview or current developments in {topic}?",
        "What is your existing understanding of {topic}?",
        "What would a useful answer look like for you regarding {topic}?",
    ],
    "command": [
        "What format would be most useful — structured outline or flowing explanation?",
        "Who is the intended audience for this {topic}?",
        "What level of detail do you need on {topic}?",
        "Is there a specific angle or perspective you want emphasised for {topic}?",
    ],
    "search": [
        "Do you want the most recent data on {topic} or a historical trend?",
        "Which geography or context matters most for {topic}?",
        "Are you looking for verified sources or a range of perspectives on {topic}?",
    ],
    "statement": [
        "What is the core question behind your statement about {topic}?",
        "What response would be most valuable to you about {topic}?",
    ],
    "reflect": [
        "What specifically prompted your reflection on {topic}?",
        "Are you seeking external perspectives or space to develop your own thinking about {topic}?",
    ],
}

_DEEPENING = [
    "And what are the second-order consequences of that?",
    "Who benefits most from this state of affairs regarding {topic}?",
    "What would change if the opposite were true about {topic}?",
    "What evidence would cause you to revise your view on {topic}?",
    "How does {topic} connect to the broader pattern you're observing?",
    "What is not being said about {topic}?",
    "Who decided the framing around {topic}, and why?",
    "What does {topic} look like from the perspective of someone with nothing to gain?",
]

_SOCRATIC = [
    "What assumption underlies your question about {topic}?",
    "Is {topic} the cause or the symptom?",
    "What would have to be true for the conventional understanding of {topic} to be wrong?",
    "Whose definition of {topic} are we using, and is it the right one?",
    "What does {topic} reveal about the system it exists within?",
    "If you already knew the answer about {topic}, what would it be?",
]

_SIMPLE_STARTERS = [
    "What do you mean by",
    "Can you say more about",
    "Why does",
    "What if",
    "Who decides",
    "What changes when",
]


class Questioner:
    """
    Generates targeted, minimal questions.
    Principle: one good question beats ten bad ones.
    The question should be so simple the answer falls out naturally.
    """

    def generate(self, comp: Comprehension, context: dict | None = None) -> QuestionSet:
        topic   = (comp.topics[0] if comp.topics else comp.keywords[0] if comp.keywords else "this")
        intent  = comp.intent
        rng     = random.Random(hash(comp.original_text))

        # Clarifying
        templates = _CLARIFY.get(intent, _CLARIFY['statement'])
        clarifying = [t.format(topic=topic) for t in rng.sample(templates, min(2, len(templates)))]

        # Deepening
        deepening = [t.format(topic=topic) for t in rng.sample(_DEEPENING, 3)]

        # Socratic
        socratic = [t.format(topic=topic) for t in rng.sample(_SOCRATIC, 2)]

        # Decide the best single question
        should_ask = self._needs_clarification(comp)
        if should_ask:
            primary = clarifying[0] if clarifying else f"What specifically about {topic} would you like to know?"
        else:
            primary = deepening[0]

        return QuestionSet(
            clarifying=clarifying,
            deepening=deepening,
            socratic=socratic,
            primary=primary,
            should_ask=should_ask,
        )

    def _needs_clarification(self, comp: Comprehension) -> bool:
        """Return True only when ambiguity genuinely blocks a good answer."""
        text = comp.original_text.strip()
        # Very short, vague queries
        if len(text.split()) <= 3:
            return True
        # No domain hints and highly complex
        if not comp.domain_hints and comp.complexity == 'complex':
            return True
        # Multiple conflicting interpretations possible
        if comp.intent_confidence < 0.6:
            return True
        return False

    def simplify_query(self, text: str) -> str:
        """
        Reduce a complex question to its atomic core.
        'What are the socioeconomic implications of quantum computing on global supply chains?'
        → 'How does quantum computing affect supply chains?'
        """
        # Strip filler phrases
        filler = re.compile(
            r'\b(please|could you|can you|would you|I was wondering|I\'d like to know|'
            r'in your opinion|from your perspective|if possible|as much detail as possible)\b',
            re.I
        )
        text = filler.sub('', text).strip()
        # Collapse multiple spaces
        text = re.sub(r'\s{2,}', ' ', text)
        # If too long, extract the core noun phrase after the question word
        if len(text.split()) > 15:
            m = re.search(r'\b(how|what|why|who|when|where)\b\s+(.{10,60}?)(?:\?|$)', text, re.I)
            if m:
                text = m.group(0).strip().rstrip('?') + '?'
        return text.capitalize()


# ── Singleton ─────────────────────────────────────────────────────────────────
_questioner = Questioner()

def generate_questions(comp: Comprehension, context: dict | None = None) -> QuestionSet:
    return _questioner.generate(comp, context)

def simplify(text: str) -> str:
    return _questioner.simplify_query(text)

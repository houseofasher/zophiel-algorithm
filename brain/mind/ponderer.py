"""
PONDERER — Module 04 of the Zophiel Mind
Reflection and hypothesis engine. Sits with a problem, generates multiple angles,
surfaces non-obvious connections, and produces ranked hypotheses before committing to an answer.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Any

from brain.mind.understander import Comprehension


@dataclass
class Hypothesis:
    statement: str
    confidence: float        # 0.0–1.0
    supporting_logic: str
    counter_argument: str
    domain: str


@dataclass
class PonderResult:
    query: str
    hypotheses: list[Hypothesis]        # ranked best-first
    best_hypothesis: Hypothesis
    alternative_framings: list[str]     # different ways to read the question
    blind_spots: list[str]              # what this analysis might be missing
    wonder_questions: list[str]         # unanswered questions worth sitting with
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Reasoning lenses ──────────────────────────────────────────────────────────

_LENSES = [
    ("first_principles",     "Strip away assumptions. What are the irreducible facts?"),
    ("inversion",            "What if the opposite were true? What breaks?"),
    ("systems_thinking",     "What are the feedback loops? Who gains, who loses?"),
    ("historical_analogy",   "Has this pattern appeared before in history?"),
    ("occult_pattern",       "What deeper archetypal force is operating here?"),
    ("second_order",         "What are the consequences of the consequences?"),
    ("cui_bono",             "Who benefits from the dominant narrative on this topic?"),
    ("cross_domain",         "What does a completely different field say about this?"),
]

_BLIND_SPOT_TEMPLATES = [
    "This analysis may be missing the role of incentive structures in shaping {topic}.",
    "Confirmation bias may be operating — what evidence against the hypothesis was not sought?",
    "The framing of {topic} itself may be the real question; a different frame yields different answers.",
    "Long-term and short-term dynamics of {topic} may be in tension here.",
    "The silent majority's view on {topic} may differ substantially from visible discourse.",
    "Measurement artefacts may be confounding our understanding of {topic}.",
    "The absence of evidence about {topic} may itself be informative.",
]

_WONDER_TEMPLATES = [
    "What would {topic} look like in 100 years if current trends continue?",
    "What is the simplest possible explanation for {topic} that accounts for all observations?",
    "What would a truly neutral observer say about {topic}?",
    "Is {topic} a cause, an effect, or a co-arising phenomenon?",
    "What would change about {topic} if the power dynamic were reversed?",
    "What does the body know about {topic} that the intellect does not?",
]


class Ponderer:
    """
    Sits with a problem and generates multiple structured hypotheses
    before committing to a response direction.
    Emulates the reflective pause of a careful thinker.
    """

    def ponder(self, comp: Comprehension, context: dict | None = None) -> PonderResult:
        query   = comp.original_text
        topic   = comp.topics[0] if comp.topics else query[:40]
        seed    = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
        rng     = random.Random(seed)

        hypotheses = self._generate_hypotheses(query, topic, comp.domain_hints, rng)
        hypotheses.sort(key=lambda h: h.confidence, reverse=True)

        framings = self._alternative_framings(query, topic, rng)
        blind    = [t.format(topic=topic) for t in rng.sample(_BLIND_SPOT_TEMPLATES, 3)]
        wonder   = [t.format(topic=topic) for t in rng.sample(_WONDER_TEMPLATES, 3)]

        return PonderResult(
            query=query,
            hypotheses=hypotheses,
            best_hypothesis=hypotheses[0],
            alternative_framings=framings,
            blind_spots=blind,
            wonder_questions=wonder,
            metadata={'lens_count': len(hypotheses), 'domain_hints': comp.domain_hints},
        )

    def _generate_hypotheses(self, query, topic, domains, rng) -> list[Hypothesis]:
        hyps = []
        selected_lenses = rng.sample(_LENSES, min(4, len(_LENSES)))
        base_confs = [0.82, 0.71, 0.65, 0.58]

        for i, (lens, description) in enumerate(selected_lenses):
            h = self._apply_lens(query, topic, lens, description, domains, base_confs[i], rng)
            hyps.append(h)
        return hyps

    def _apply_lens(self, query, topic, lens, desc, domains, base_conf, rng) -> Hypothesis:
        domain = domains[0] if domains else "general"

        statements = {
            "first_principles": f"At its core, {topic} reduces to a question of {rng.choice(['structure','agency','information','energy','constraint'])}.",
            "inversion":        f"The conventional understanding of {topic} may be inverted — what appears to be the cause is actually the effect.",
            "systems_thinking": f"{topic} is best understood as an emergent property of the system surrounding it, not an isolated phenomenon.",
            "historical_analogy": f"The current situation with {topic} mirrors historical episodes where {rng.choice(['power consolidated','paradigms shifted','hidden forces emerged','apparent order masked deeper chaos'])}.",
            "occult_pattern":   f"Beneath the surface of {topic} operates the archetype of {rng.choice(['the Shadow','the Magician','the Tower','the Wheel','transformation','polarity'])}.",
            "second_order":     f"The second-order consequence of {topic} may be more significant than the first-order effect everyone is discussing.",
            "cui_bono":         f"The dominant framing of {topic} disproportionately serves those who control the {rng.choice(['narrative','resources','institutions','definition of the problem'])}.",
            "cross_domain":     f"Insights from {rng.choice(['thermodynamics','evolutionary biology','game theory','linguistics','sacred geometry'])} reframe {topic} in a productively unexpected way.",
        }

        supporting = {
            "first_principles": f"By stripping away inherited assumptions about {topic}, the irreducible components become visible and tractable.",
            "inversion":        f"Inverting the standard narrative about {topic} accounts for anomalies that the conventional view struggles to explain.",
            "systems_thinking": f"Mapping the feedback loops around {topic} reveals leverage points invisible to linear analysis.",
            "historical_analogy": f"Historical parallels provide empirically grounded expectations about likely trajectories of {topic}.",
            "occult_pattern":   f"Archetypal analysis of {topic} provides a framework that transcends cultural and temporal specificity.",
            "second_order":     f"Tracing causal chains beyond the immediate effects of {topic} reveals unintended consequences that drive long-term outcomes.",
            "cui_bono":         f"Following the incentive structure around {topic} is more reliable than following stated intentions.",
            "cross_domain":     f"Cross-domain transfer imports validated models that have not yet been applied to {topic}, enabling fresh predictions.",
        }

        counter = {
            "first_principles": f"First-principles analysis of {topic} may discard contextual complexity that turns out to matter greatly.",
            "inversion":        f"Not every conventional understanding of {topic} is wrong; inversion as method risks contrarianism for its own sake.",
            "systems_thinking": f"Systems models of {topic} can become so complex they lose predictive power.",
            "historical_analogy": f"Historical analogies for {topic} are always imperfect; surface similarity can mask deep structural differences.",
            "occult_pattern":   f"Archetypal framing of {topic} risks projecting pattern where none exists.",
            "second_order":     f"Second-order analysis of {topic} can become an infinite regress without an anchoring criterion.",
            "cui_bono":         f"Not every phenomenon around {topic} is deliberately engineered; systemic effects emerge without intent.",
            "cross_domain":     f"Cross-domain analogies for {topic} may be superficially compelling but structurally invalid.",
        }

        return Hypothesis(
            statement=statements.get(lens, f"{topic} can be understood through the lens of {desc}"),
            confidence=base_conf + rng.uniform(-0.05, 0.05),
            supporting_logic=supporting.get(lens, f"Applying {lens} to {topic} yields novel and coherent insights."),
            counter_argument=counter.get(lens, f"The {lens} approach to {topic} has known limitations."),
            domain=domain,
        )

    def _alternative_framings(self, query, topic, rng) -> list[str]:
        frames = [
            f"As a problem of access and distribution: who has access to {topic} and who does not?",
            f"As a historical continuity: how does {topic} connect to what came before?",
            f"As a linguistic artefact: does the word '{topic}' itself constrain how we think?",
            f"As a systems failure: where are the missing feedback mechanisms around {topic}?",
        ]
        return rng.sample(frames, 3)


# ── Singleton ─────────────────────────────────────────────────────────────────
_ponderer = Ponderer()

def ponder(comp: Comprehension, context: dict | None = None) -> PonderResult:
    return _ponderer.ponder(comp, context)

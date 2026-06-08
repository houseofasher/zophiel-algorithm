"""
CROSS-DOMAIN REASONER — Module 09 of the Zophiel Mind
Connects knowledge across different domains.
The smartest thinkers answer questions in one domain using insights from another.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CrossDomainInsight:
    query: str
    primary_domain: str
    analogy_domain: str
    structural_parallel: str
    transferred_insight: str
    confidence: float
    bridging_concept: str


@dataclass
class CrossDomainResult:
    query: str
    insights: list[CrossDomainInsight]
    synthesis: str
    bridging_concepts: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Domain bridge map — what every domain can borrow from ────────────────────

BRIDGES = {
    "science":      ["systems thinking", "feedback loops", "emergence", "entropy", "equilibrium"],
    "mathematics":  ["optimization", "proof by contradiction", "symmetry", "recursion", "convergence"],
    "medicine":     ["diagnosis under uncertainty", "dose-response", "immunity", "healing cycles", "triage"],
    "technology":   ["abstraction layers", "modularity", "debugging", "version control", "protocols"],
    "philosophy":   ["first principles", "epistemology", "ontology", "dialectic", "phenomenology"],
    "history":      ["cycles of empire", "precedent", "historical analogy", "long arcs", "unintended consequences"],
    "economics":    ["incentive structures", "marginal analysis", "supply/demand", "externalities", "network effects"],
    "occult":       ["as above so below", "polarity", "archetype", "hidden forces", "will and manifestation"],
    "psychology":   ["shadow integration", "projection", "cognitive bias", "trauma response", "ego structure"],
    "nature":       ["evolution", "adaptation", "predator-prey", "symbiosis", "carrying capacity"],
    "military":     ["strategy", "deception", "supply lines", "fog of war", "terrain advantage"],
    "music":        ["harmony", "rhythm", "counterpoint", "improvisation", "tension and release"],
}

# ── Cross-domain insight templates ───────────────────────────────────────────

_INSIGHT_TEMPLATES = [
    "{analogy_domain} teaches us that in {primary_domain}, {concept} operates like {parallel}.",
    "The {concept} from {analogy_domain} maps directly onto {primary_domain}: {parallel}.",
    "Just as {analogy_domain} reveals {concept}, {primary_domain} exhibits the same underlying structure: {parallel}.",
]

_PARALLELS = {
    ("science", "occult"):      ("entropy is disorder seeking equilibrium", "chaos preceding new order"),
    ("economics", "nature"):    ("market equilibrium", "ecological balance via predation and resource limits"),
    ("technology", "military"): ("abstraction layers", "command hierarchies that separate strategy from tactics"),
    ("medicine", "philosophy"): ("diagnosis under uncertainty", "socratic questioning to find root causes"),
    ("history", "mathematics"): ("cycles of empire", "periodic functions — rise, peak, decay, renewal"),
    ("psychology", "occult"):   ("shadow integration", "confronting the dark side to achieve wholeness"),
    ("science", "music"):       ("harmonic oscillation", "standing waves and resonance in physical systems"),
    ("economics", "military"):  ("incentive structures", "rational actor theory and strategic deception"),
}


class CrossDomainReasoner:
    """
    Answers questions by finding structural parallels across domains.
    The best answers transcend the domain of the question.
    """

    def reason(self, query: str, primary: str, all_domains: list[str]) -> CrossDomainResult:
        insights = []
        for analogy_d, concepts in BRIDGES.items():
            if analogy_d == primary:
                continue
            parallel_key = tuple(sorted([primary, analogy_d]))
            parallel = _PARALLELS.get(parallel_key, ("", "the same structural principle"))
            if not parallel[0]:
                parallel = (concepts[0], f"the {concepts[0]} principle applied to {primary}")
            concept = concepts[0]
            stmt = f"In {primary}, {concept} from {analogy_d} reveals: {parallel[1]}."
            insights.append(CrossDomainInsight(
                query=query,
                primary_domain=primary,
                analogy_domain=analogy_d,
                structural_parallel=parallel[1],
                transferred_insight=stmt,
                confidence=0.65,
                bridging_concept=concept,
            ))

        # Sort by structural relevance (prefer occult, nature, mathematics)
        priority = {"occult": 1, "nature": 2, "mathematics": 3, "history": 4}
        insights.sort(key=lambda i: priority.get(i.analogy_domain, 10))
        top = insights[:4]

        synthesis = self._synthesise(query, primary, top)
        bridges   = list({i.bridging_concept for i in top})

        return CrossDomainResult(
            query=query,
            insights=top,
            synthesis=synthesis,
            bridging_concepts=bridges,
            metadata={"primary_domain": primary, "analogy_count": len(top)},
        )

    def _synthesise(self, query: str, primary: str, insights: list[CrossDomainInsight]) -> str:
        if not insights:
            return ""
        top = insights[0]
        # Return a short, additive insight — not a frame that overrides the main answer
        return (
            f"Interestingly, the same pattern shows up in {top.analogy_domain}: "
            f"{top.structural_parallel}."
        )

    def quick_bridge(self, domain: str) -> str:
        concepts = BRIDGES.get(domain.lower(), BRIDGES["philosophy"])
        return concepts[0]


_reasoner = CrossDomainReasoner()

def reason(query: str, primary: str, domains: list[str] | None = None) -> CrossDomainResult:
    return _reasoner.reason(query, primary, domains or [])

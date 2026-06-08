"""PISP Framework — Pre-Ignition Synthesis Protocol.

Zophiel's operational intelligence loop for query processing.
Implements the 7-phase intelligence cycle:
  INPUT → DECONSTRUCT → RESEARCH → SYNTHESIZE → PLAN → COMMIT → BUILD

This is the meta-cognitive layer that runs before any answer generation.
It determines HOW to approach the query, not just WHAT to return.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

# PISP Phase names
PISPPhase = Literal[
    "INPUT",
    "DECONSTRUCT",
    "RESEARCH",
    "SYNTHESIZE",
    "PLAN",
    "COMMIT",
    "BUILD",
]

# Query classification
QueryClass = Literal[
    "factual",         # Has a verifiable answer
    "analytical",      # Requires reasoning + breakdown
    "philosophical",   # Requires metaphysical + ethical reasoning
    "operational",     # How-to, build, execute
    "predictive",      # Future state reasoning
    "psychological",   # Human behavior analysis
    "esoteric",        # Occult/spiritual/metaphysical
    "unknown",
]

# Confidence grades
ConfidenceGrade = Literal["SIGNAL", "PROBABLE", "THEORETICAL", "SPECULATIVE", "NOISE"]

# Confidence thresholds
_CONFIDENCE_THRESHOLDS: dict[ConfidenceGrade, tuple[float, float]] = {
    "SIGNAL":      (0.85, 1.00),  # Hard data, direct match
    "PROBABLE":    (0.65, 0.85),  # Strong pattern match
    "THEORETICAL": (0.40, 0.65),  # Logical deduction, limited data
    "SPECULATIVE": (0.20, 0.40),  # Pattern extrapolation
    "NOISE":       (0.00, 0.20),  # Insufficient data
}


@dataclass
class PISPDeconstruction:
    """DECONSTRUCT phase output — breaks the query into its components."""
    surface_question: str        # What they literally asked
    real_question: str           # What they actually want to know
    hidden_assumption: str       # What assumption underlies the question
    query_class: QueryClass
    domain_hints: list[str]      # Subject domains detected
    complexity: float            # 0.0 = simple, 1.0 = maximum complexity
    is_multi_part: bool          # Does the query have multiple sub-questions?


@dataclass
class PISPResearchPlan:
    """RESEARCH phase — what sources and approaches to use."""
    knowledge_sources: list[str]      # e.g. ["corpus_rag", "asher_logic", "esoteric_kb"]
    search_queries: list[str]         # Derived search queries for RAG
    requires_calculation: bool
    requires_3layer_decode: bool      # Use Asher's 3-layer decode
    requires_esoteric: bool           # Use Zophiel knowledge base
    requires_causal_chain: bool       # Build X=Y=Z chains
    parallel_search_possible: bool


@dataclass
class PISPSynthesis:
    """SYNTHESIZE phase — combining research into a coherent answer."""
    primary_insight: str              # The core truth
    supporting_evidence: list[str]    # Data points supporting it
    contradictions_found: list[str]   # Any conflicting information
    confidence_score: float
    confidence_grade: ConfidenceGrade
    unresolved_gaps: list[str]        # What we couldn't determine


@dataclass
class PISPPlan:
    """PLAN phase — response strategy."""
    response_structure: str           # How to structure the output
    opening_approach: str             # How to open the response
    key_points_order: list[str]       # What order to present insights
    use_equation_logic: bool          # Use X=Y=Z chains
    use_3layer_decode: bool           # Use surface/mechanism/truth
    response_length: str              # "brief", "moderate", "detailed"


@dataclass
class PISPResult:
    """Full PISP analysis result."""
    query: str
    deconstruction: PISPDeconstruction
    research_plan: PISPResearchPlan
    synthesis: PISPSynthesis | None
    plan: PISPPlan
    current_phase: PISPPhase


# Query classification patterns
_QUERY_CLASS_PATTERNS: list[tuple[list[str], QueryClass]] = [
    (["how does", "what is", "who is", "when did", "where is", "define", "explain"],
     "factual"),
    (["why", "analyze", "compare", "examine", "evaluate", "assess", "what causes"],
     "analytical"),
    (["what is the meaning", "is there a god", "consciousness", "free will",
      "purpose of", "truth about", "what is reality", "philosophy"],
     "philosophical"),
    (["how to", "how do i", "build", "create", "make", "implement", "code", "write"],
     "operational"),
    (["will", "predict", "forecast", "future", "what will happen", "probability"],
     "predictive"),
    (["why do people", "human behavior", "psychology", "why does he", "why does she",
      "attachment", "manipulation", "emotion", "trauma"],
     "psychological"),
    (["occult", "spiritual", "monad", "demiurge", "astrology", "kabbalah", "biblical",
      "esoteric", "mystical", "symbolism", "messiah", "divine", "soul", "karma"],
     "esoteric"),
]


def _classify_query(query: str) -> QueryClass:
    """Classify the query into one of the QueryClass categories."""
    ql = query.lower()
    for patterns, qclass in _QUERY_CLASS_PATTERNS:
        for pattern in patterns:
            if pattern in ql:
                return qclass
    return "analytical"  # default


def _detect_domains(query: str) -> list[str]:
    """Detect subject domains from query keywords."""
    ql = query.lower()
    domains: list[str] = []
    domain_map = {
        "science": ["biology", "physics", "chemistry", "science", "evolution", "dna"],
        "technology": ["code", "software", "algorithm", "computer", "ai", "programming"],
        "finance": ["money", "invest", "market", "stock", "crypto", "trade", "wealth"],
        "spirituality": ["soul", "spirit", "god", "divine", "monad", "consciousness", "karma"],
        "psychology": ["behavior", "emotion", "mind", "trauma", "attachment", "anxiety"],
        "history": ["history", "ancient", "historical", "civilization", "empire"],
        "astrology": ["zodiac", "planet", "saturn", "jupiter", "mercury", "venus", "mars"],
    }
    for domain, keywords in domain_map.items():
        if any(kw in ql for kw in keywords):
            domains.append(domain)
    return domains or ["general"]


def _compute_complexity(query: str) -> float:
    """Estimate query complexity 0.0-1.0."""
    score = 0.0
    words = query.split()
    # Length contribution
    score += min(0.3, len(words) / 100)
    # Multi-part detection
    if any(c in query for c in ["?", ",", " and ", " also ", " plus "]):
        score += 0.2
    # Philosophical/abstract terms
    abstract_terms = ["meaning", "truth", "consciousness", "reality", "existence",
                      "purpose", "divine", "universe", "infinite"]
    score += sum(0.05 for t in abstract_terms if t in query.lower())
    return min(1.0, score)


class PISPFramework:
    """Pre-Ignition Synthesis Protocol — Zophiel's meta-cognitive query processor."""

    def run(self, query: str, context: str = "") -> PISPResult:
        """Run the full PISP cycle on a query.

        Returns a PISPResult that tells the orchestrator HOW to process the query.
        The synthesis field is None at this stage — it gets filled after RAG retrieval.
        """
        # PHASE 1: INPUT — receive and validate
        query = query.strip()

        # PHASE 2: DECONSTRUCT — understand what's really being asked
        deconstruction = self._deconstruct(query, context)

        # PHASE 3: RESEARCH — plan what sources to use
        research_plan = self._plan_research(deconstruction)

        # PHASE 4: SYNTHESIZE — placeholder (filled after RAG)
        # PHASE 5: PLAN — decide response structure
        plan = self._plan_response(deconstruction, research_plan)

        return PISPResult(
            query=query,
            deconstruction=deconstruction,
            research_plan=research_plan,
            synthesis=None,
            plan=plan,
            current_phase="RESEARCH",
        )

    def synthesize(self, result: PISPResult, evidence: list[str],
                   confidence: float) -> PISPResult:
        """Fill in the synthesis phase after evidence is gathered."""
        grade = self._grade_confidence(confidence)

        synthesis = PISPSynthesis(
            primary_insight="",   # To be filled by orchestrator
            supporting_evidence=evidence[:5],
            contradictions_found=[],
            confidence_score=confidence,
            confidence_grade=grade,
            unresolved_gaps=[],
        )

        result.synthesis = synthesis
        result.current_phase = "SYNTHESIZE"
        return result

    def _deconstruct(self, query: str, context: str) -> PISPDeconstruction:
        """Break query into surface/real/hidden components."""
        qclass = _classify_query(query)
        domains = _detect_domains(query)
        complexity = _compute_complexity(query)

        # Surface question = the literal query
        surface = query

        # Real question — what they actually want
        # Heuristic: strip question words and get to the noun phrase
        real = re.sub(
            r"^(what is|who is|how does|can you explain|tell me about|"
            r"what do you think about|i want to know)\s+",
            "", query, flags=re.IGNORECASE
        ).strip()
        if not real:
            real = query

        # Hidden assumption — what the question takes for granted
        hidden = self._detect_hidden_assumption(query, qclass)

        # Multi-part detection
        is_multi = len(re.findall(r"[?]", query)) > 1 or " and " in query.lower()

        return PISPDeconstruction(
            surface_question=surface,
            real_question=real,
            hidden_assumption=hidden,
            query_class=qclass,
            domain_hints=domains,
            complexity=round(complexity, 2),
            is_multi_part=is_multi,
        )

    def _detect_hidden_assumption(self, query: str, qclass: QueryClass) -> str:
        """Infer what the question assumes without being asked."""
        ql = query.lower()
        if qclass == "philosophical":
            return "Assumes objective truth is accessible through language."
        if qclass == "esoteric":
            return "Assumes esoteric frameworks map to verifiable patterns."
        if "best" in ql or "better" in ql:
            return "Assumes a universal standard for quality exists."
        if "why do people" in ql:
            return "Assumes human behavior follows predictable patterns."
        if "will" in ql:
            return "Assumes the future is partially deterministic and deducible."
        return "No dominant hidden assumption detected."

    def _plan_research(self, dec: PISPDeconstruction) -> PISPResearchPlan:
        """Determine which knowledge sources to activate."""
        sources: list[str] = ["corpus_rag"]

        requires_3layer = dec.query_class in ("analytical", "esoteric", "philosophical")
        requires_esoteric = dec.query_class == "esoteric" or "spirituality" in dec.domain_hints
        requires_causal = dec.query_class == "analytical" or "technology" in dec.domain_hints
        requires_calc = any(c.isdigit() for c in dec.surface_question)

        if requires_3layer:
            sources.append("asher_logic_engine")
        if requires_esoteric:
            sources.append("zophiel_knowledge_base")
        if requires_calc:
            sources.append("fast_path_calculator")

        # Generate search queries — the real question + domain-specific variants
        search_queries = [dec.real_question]
        for domain in dec.domain_hints[:2]:
            if domain != "general":
                search_queries.append(f"{domain}: {dec.real_question}")

        return PISPResearchPlan(
            knowledge_sources=sources,
            search_queries=search_queries[:3],
            requires_calculation=requires_calc,
            requires_3layer_decode=requires_3layer,
            requires_esoteric=requires_esoteric,
            requires_causal_chain=requires_causal,
            parallel_search_possible=len(sources) > 1,
        )

    def _plan_response(self, dec: PISPDeconstruction,
                       research: PISPResearchPlan) -> PISPPlan:
        """Determine response structure and presentation strategy."""
        # Length based on complexity
        if dec.complexity < 0.3:
            length = "brief"
        elif dec.complexity < 0.65:
            length = "moderate"
        else:
            length = "detailed"

        # Opening approach
        openings = {
            "factual":      "Lead with the core fact. No preamble.",
            "analytical":   "Lead with the pattern. Then the mechanics. Then the truth.",
            "philosophical":"Lead with the question's hidden assumption. Then decode it.",
            "operational":  "Lead with the first actionable step.",
            "predictive":   "Lead with the most probable outcome. Grade the confidence.",
            "psychological":"Lead with the behavioral pattern. No moralizing.",
            "esoteric":     "Lead with the surface decode. Then go deeper.",
        }
        opening = openings.get(dec.query_class, "Lead with the core insight.")

        # Key points order
        if research.requires_3layer_decode:
            key_points = ["surface_observation", "mechanism_decode", "divine_truth"]
        elif research.requires_causal_chain:
            key_points = ["equation_chain", "pattern_recognition", "conclusion"]
        else:
            key_points = ["primary_answer", "supporting_evidence", "confidence"]

        return PISPPlan(
            response_structure="declarative_lines" if dec.complexity < 0.5 else "structured_paragraphs",
            opening_approach=opening,
            key_points_order=key_points,
            use_equation_logic=research.requires_causal_chain,
            use_3layer_decode=research.requires_3layer_decode,
            response_length=length,
        )

    @staticmethod
    def _grade_confidence(score: float) -> ConfidenceGrade:
        """Convert numeric confidence to grade label."""
        for grade, (low, high) in _CONFIDENCE_THRESHOLDS.items():
            if low <= score <= high:
                return grade
        return "NOISE"


# Module-level singleton
_FRAMEWORK: PISPFramework | None = None


def get_pisp() -> PISPFramework:
    global _FRAMEWORK
    if _FRAMEWORK is None:
        _FRAMEWORK = PISPFramework()
    return _FRAMEWORK


def analyze(query: str, context: str = "") -> PISPResult:
    """Convenience function — run PISP analysis."""
    return get_pisp().run(query, context)

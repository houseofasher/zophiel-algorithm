"""
Analogy Engine — Generates structural analogies to clarify abstract concepts.
Maps source domain → target domain using relational structure, producing
"X is to Y as A is to B" style analogies and metaphorical bridges.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field

_ANALOGIES: dict[str, list[tuple[str, str]]] = {
    'electricity': [
        ('water pressure', 'voltage drives current the way water pressure drives flow'),
        ('highway traffic', 'current in a conductor is like cars on a highway: resistance is the bottleneck'),
    ],
    'dna': [
        ('recipe book', 'DNA is the recipe book; a gene is a single recipe; a protein is the dish'),
        ('blueprint', 'DNA is the blueprint; ribosomes are the construction crew'),
    ],
    'entropy': [
        ('shuffled deck', 'entropy is like a shuffled deck: there are vastly more disordered arrangements than ordered ones'),
        ('spreading ink', 'entropy increases like ink dropping into water — disorder spreads spontaneously'),
    ],
    'neural network': [
        ('brain synapse', 'weights in a neural network are like synaptic strengths — reinforced by repeated activation'),
        ('committee vote', 'each layer votes on features; the final layer reaches a consensus decision'),
    ],
    'evolution': [
        ('editing manuscript', 'evolution edits the genome the way a careless editor makes random changes — selection keeps the good ones'),
        ('market competition', 'species compete for niches like firms compete for market share; the fittest survive'),
    ],
    'gravity': [
        ('bowling ball on sheet', 'mass curves spacetime like a bowling ball curves a rubber sheet'),
        ('funnel', 'orbital decay is like a marble spiralling into a funnel'),
    ],
    'compound interest': [
        ('snowball', 'compound interest grows like a snowball rolling downhill — size feeds more size'),
    ],
    'immune system': [
        ('army', 'the immune system is an army: B-cells are scouts that remember the enemy; T-cells are soldiers that attack'),
        ('lock and key', 'antibodies bind pathogens like a lock and key — specificity is the defence'),
    ],
    'democracy': [
        ('marketplace of ideas', 'democracy is a marketplace of ideas where votes are currency'),
        ('referee', 'the constitution is the rulebook; courts are referees'),
    ],
    'memory': [
        ('RAM and hard drive', 'working memory is RAM — fast, limited; long-term memory is the hard drive — slow, vast'),
        ('index card', 'each memory is an index card; retrieval is searching the filing cabinet'),
    ],
}

_STRUCTURAL = [
    ("atom", "solar system", "electrons orbit the nucleus the way planets orbit the sun"),
    ("gene", "recipe", "genes encode proteins the way recipes encode meals"),
    ("logic proof", "building construction", "axioms are foundations; theorems are floors built atop them"),
    ("language grammar", "traffic law", "grammar rules coordinate meaning the way traffic laws coordinate movement"),
    ("enzyme", "lock and key", "enzymes bind substrates via complementary shapes, like a lock accepting only its key"),
    ("paradigm shift", "revolution", "scientific revolutions overturn paradigms the way political revolutions overturn governments"),
]

@dataclass
class AnalogyResult:
    source_concept: str
    analogies: list[str]
    structural_mapping: str
    best_analogy: str

def generate_analogy(concept: str, context: str = '') -> AnalogyResult:
    concept_lower = concept.lower()
    found: list[str] = []

    for key, pairs in _ANALOGIES.items():
        if key in concept_lower or concept_lower in key:
            for _, description in pairs:
                found.append(description)

    # Keyword search in context
    if not found and context:
        ctx_lower = context.lower()
        for key, pairs in _ANALOGIES.items():
            if key in ctx_lower:
                for _, description in pairs:
                    found.append(description)

    # Structural fallback
    struct = ''
    for src, tgt, mapping in _STRUCTURAL:
        if src in concept_lower or tgt in concept_lower:
            struct = mapping
            break

    if not found and not struct:
        # Generic fallogy
        words = re.findall(r'\b[a-z]{4,}\b', concept_lower)
        if words:
            found.append(
                f"{concept} can be understood like a system where inputs are transformed "
                f"into outputs through a structured process — much like a machine converts raw material into a product."
            )

    best = found[0] if found else (struct or f"{concept} operates according to systematic principles.")
    return AnalogyResult(
        source_concept=concept,
        analogies=found[:3],
        structural_mapping=struct,
        best_analogy=best,
    )

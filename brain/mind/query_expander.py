"""
Query Expander — Enriches a user query with related terms before RAG retrieval.
Prevents zero-hit failures and domain confusion by mapping common terms to
synonyms and domain-signal words that exist in the corpus.
"""
from __future__ import annotations
import re

_EXPANSIONS: dict[str, list[str]] = {
    # Biology
    'evolution':       ['darwinian natural selection', 'darwin biology', 'mutation species', 'fitness organism', 'biological evolution'],
    'vaccine':         ['antibody', 'immune', 'pathogen', 'B cell', 'T cell', 'immunity'],
    'immune':          ['antibody', 'lymphocyte', 'pathogen', 'vaccine', 'T cell'],
    'dna':             ['replication', 'chromosome', 'gene', 'nucleotide', 'base pair'],
    'cell':            ['mitosis', 'nucleus', 'membrane', 'organelle', 'cytoplasm'],
    'photosynthesis':  ['chlorophyll', 'chloroplast', 'glucose', 'carbon dioxide', 'light'],
    'protein':         ['amino acid', 'ribosome', 'enzyme', 'peptide', 'fold'],
    # Physics
    'entropy':         ['thermodynamics', 'disorder', 'Boltzmann', 'second law', 'heat'],
    'quantum':         ['uncertainty', 'wavefunction', 'Schrodinger', 'superposition', 'photon'],
    'relativity':      ['Einstein', 'spacetime', 'speed of light', 'time dilation', 'gravity'],
    'gravity':         ['Einstein', 'mass', 'Newton', 'general relativity', 'acceleration'],
    'black hole':      ['event horizon', 'Schwarzschild', 'singularity', 'gravity', 'spacetime'],
    # Computer Science
    'tcp':             ['network', 'protocol', 'reliable', 'connection', 'handshake'],
    'udp':             ['network', 'protocol', 'datagram', 'connectionless', 'packet'],
    'backpropagation': ['gradient', 'neural network', 'chain rule', 'loss', 'weight'],
    'neural network':  ['backpropagation', 'gradient', 'layer', 'weight', 'activation'],
    'algorithm':       ['complexity', 'time', 'sorting', 'search', 'big-O'],
    'machine learning':['gradient', 'training', 'neural network', 'model', 'data'],
    # Chemistry
    'acid':            ['pH', 'proton', 'base', 'dissociation', 'Ka'],
    'reaction':        ['activation energy', 'catalyst', 'equilibrium', 'Arrhenius', 'rate'],
    'bond':            ['covalent', 'ionic', 'electronegativity', 'electron', 'atom'],
    # Philosophy / Ethics
    'categorical imperative': ['Kant', 'maxim', 'universalizable', 'duty', 'rational'],
    'utilitarian':     ['utility', 'happiness', 'Bentham', 'Mill', 'consequence'],
    'utilitarianism':  ['utility', 'happiness', 'Bentham', 'Mill', 'consequence'],
    'utilitarian':     ['utility', 'happiness', 'Bentham', 'Mill', 'consequence'],
    'ethics':          ['moral', 'virtue', 'duty', 'consequence', 'right'],
    'consciousness':   ['mind', 'qualia', 'experience', 'brain', 'perception'],
    # Economics
    'supply':          ['demand', 'price', 'market', 'equilibrium', 'quantity'],
    'demand':          ['supply', 'price', 'market', 'consumer', 'elasticity'],
    'inflation':       ['monetary', 'price', 'interest rate', 'central bank', 'currency'],
    'capitalism':      ['market', 'private', 'profit', 'competition', 'investment'],
    # Environment
    'climate':         ['CO2', 'greenhouse', 'temperature', 'carbon', 'warming'],
    'global warming':  ['CO2', 'greenhouse', 'temperature', 'carbon', 'feedback'],
    'ecosystem':       ['biodiversity', 'species', 'habitat', 'food chain', 'population'],
    # Medicine
    'diabetes':        ['insulin', 'glucose', 'pancreas', 'blood sugar', 'type'],
    'cancer':          ['tumor', 'mutation', 'cell', 'oncogene', 'metastasis'],
    'antibiotic':      ['bacteria', 'resistance', 'penicillin', 'cell wall', 'infection'],
    # Astronomy
    'star':            ['stellar', 'fusion', 'luminosity', 'spectral', 'main sequence'],
    'galaxy':          ['milky way', 'spiral', 'dark matter', 'cosmic', 'star'],
    'big bang':        ['cosmic', 'expansion', 'Hubble', 'radiation', 'universe'],
}

_DOMAIN_SIGNALS: dict[str, str] = {
    'biology':      'biology cell dna organism',
    'physics':      'physics energy force quantum',
    'chemistry':    'chemistry molecule reaction bond',
    'computer science': 'algorithm software network code',
    'mathematics':  'mathematics proof theorem equation',
    'ethics':       'ethics moral virtue duty',
    'economics':    'economics market supply demand',
    'medicine':     'medicine disease treatment clinical',
    'environment':  'environment climate carbon ecosystem',
    'psychology':   'psychology mind behavior cognitive',
    'astronomy':    'astronomy star galaxy space',
    'history':      'history century civilization event',
    'philosophy':   'philosophy epistemology logic reason',
    'law':          'law legal rights justice',
}

def expand_query(query: str, detected_domain: str = '') -> str:
    """
    Expand a query with related terms to improve RAG retrieval recall.
    Prepends domain signal if domain is known.
    Returns enriched query string.
    """
    q_lower = query.lower()
    additions: list[str] = []

    # Add domain signal words first (boosts domain-correct docs)
    if detected_domain:
        domain_key = detected_domain.lower()
        for key, signal in _DOMAIN_SIGNALS.items():
            if key in domain_key or domain_key in key:
                additions.append(signal)
                break

    # Add per-term expansions
    for term, synonyms in _EXPANSIONS.items():
        if term in q_lower:
            additions.extend(synonyms[:3])  # top 3 synonyms only

    if not additions:
        return query

    expanded = query + ' ' + ' '.join(additions)
    return expanded

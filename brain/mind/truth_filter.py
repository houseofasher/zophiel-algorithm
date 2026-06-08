"""
TRUTH FILTER — Module 13 of the Zophiel Mind
Python port of the Zophiel Engine retrieval-ranker.
Scores sentences from live web documents for relevance and credibility.
Distinguishes definition sentences from general claims.
Detects noise, promotional content, and low-quality sources.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class LiveDocument:
    text: str
    url: str
    title: str
    source: str = "live"    # must be "live" — never test fixtures
    fetched_at: str = ""


@dataclass
class RankedSentence:
    sentence: str
    url: str
    title: str
    score: float


@dataclass
class TruthResult:
    query: str
    top_sentences: list[RankedSentence]
    best_answer: str
    source_urls: list[str]
    credibility: float        # 0.0–1.0
    narrative_bias: list[str]  # detected framing biases
    verdict: str              # "reliable" | "mixed" | "unreliable" | "no_data"
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Stop words ────────────────────────────────────────────────────────────────

_STOPWORDS = {
    "the","and","for","are","you","what","how","why","can","does",
    "was","were","who","when","where","which","that","this","about",
    "from","have","with","been","they","their","will","would","could",
    "also","than","then","these","those","into","more","some","been",
}

# ── Sentence quality patterns ─────────────────────────────────────────────────

_DEFINITION_CUES = re.compile(
    r'^(?:what\s+(?:is|are)|who\s+(?:is|are)|define|explain(?:\s+what)?|describe|tell\s+me\s+about)\s+(.+?)\??$',
    re.I
)
_DEFINITION_SENTENCE = re.compile(
    r'\b(is|are|was|were|means|refers?\s+to|defined\s+as|consists\s+of|involves|describes|known\s+as)\b',
    re.I
)
_SUBJECT_FIRST = re.compile(
    r'^(?:an?\s+)?[a-z][\w\s\-]{0,60}\s+(is|are|was|were)\s+(?:a|an|the)\b',
    re.I
)
_NOISE = re.compile(
    r'\b(github|click here|sign up|subscribe|cookie|privacy policy|terms of service|'
    r'download now|get started|our platform|self-evolving memory|portable memory layer)\b',
    re.I
)
_ACADEMIC_NOISE = re.compile(
    r'\b(comments:\s*\d+\s+pages|subjects:|figures,\s+\d+\s+appendices|arxiv:|doi:|'
    r'(?:vol\.|pp\.)\s*\d)\b',
    re.I
)
_EDUCATIONAL_HOSTS = {
    'arxiv.org','britannica.com','wikipedia.org','worldhistory.org',
    'paperswithcode.com','nature.com','ncbi.nlm.nih.gov','pubmed.ncbi.nlm.nih.gov',
    'scholar.google.com','jstor.org','sciencedirect.com','researchgate.net',
    'plos.org','bbc.com','reuters.com','apnews.com',
}

# ── Credibility signals ───────────────────────────────────────────────────────

_CREDIBLE_PATTERNS = re.compile(
    r'\b(study|research|published|peer.reviewed|journal|evidence|data|findings|survey|'
    r'analysis|measured|observed|experiment|trial|meta.analysis)\b', re.I
)
_UNRELIABLE_PATTERNS = re.compile(
    r'\b(they don\'t want you to know|secret|hidden truth|mainstream media|wake up|'
    r'sheeple|plandemic|deep state|elites are|globalists)\b', re.I
)
_HEDGE_PATTERNS = re.compile(
    r'\b(allegedly|reportedly|claimed|sources say|according to|unverified|'
    r'rumoured|speculated)\b', re.I
)

# ── Bias/narrative markers ────────────────────────────────────────────────────

_BIAS_MARKERS = {
    "technocratic_narrative": re.compile(r'\b(AI will replace|automation|disruption|innovation|digital transformation)\b', re.I),
    "fear_narrative":         re.compile(r'\b(danger|threat|crisis|emergency|catastrophic|devastating|alarming)\b', re.I),
    "authority_narrative":    re.compile(r'\b(experts say|officials confirm|government states|scientists agree|CDC|WHO)\b', re.I),
    "optimism_bias":          re.compile(r'\b(breakthrough|revolutionary|game.changing|unprecedented|historic)\b', re.I),
}


def _host_of(url: str) -> str:
    try:
        h = urlparse(url).hostname or ""
        return h.replace("www.", "").lower()
    except Exception:
        return ""


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r'[a-z0-9]{3,}', text.lower())
    return list(dict.fromkeys(t for t in tokens if t not in _STOPWORDS))


def _split_sentences(text: str) -> list[str]:
    text = re.sub(r'\s+', ' ', text)
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in parts if 40 <= len(s.strip()) <= 520]


def _term_matches(text: str, term: str) -> bool:
    if term in text:
        return True
    if term.endswith('s') and len(term) > 4 and term[:-1] in text:
        return True
    if not term.endswith('s') and f"{term}s" in text:
        return True
    return False


def _score_sentence(sentence: str, terms: list[str], kind: str, doc: LiveDocument,
                    seed_hosts: set[str], raw_focus: str) -> float:
    lowered    = sentence.lower()
    title_low  = doc.title.lower()
    host       = _host_of(doc.url)

    if not terms:
        return 0.0

    matched = [t for t in terms if _term_matches(lowered, t) or _term_matches(title_low, t)]
    if not matched:
        return 0.0

    coverage = len(matched) / len(terms)
    score    = len(matched) + coverage * 2.0

    if any(t in title_low for t in terms):
        score += 1.5

    if kind == "definition":
        if _DEFINITION_SENTENCE.search(sentence) or _SUBJECT_FIRST.match(sentence):
            score += 4.0
        if _NOISE.search(sentence):
            score -= 6.0
        if _ACADEMIC_NOISE.search(sentence):
            score -= 5.0
        if 'github.com' in doc.url:
            score -= 5.0
        if raw_focus and raw_focus.lower() in lowered:
            score += 2.0

    # Educational host boost
    for edu in _EDUCATIONAL_HOSTS:
        if host == edu or host.endswith(f'.{edu}'):
            score += 1.0
            break

    # Seed host boost
    for sh in seed_hosts:
        if host == sh or host.endswith(f'.{sh}'):
            score += 2.0
            break

    return score


def _credibility_score(docs: list[LiveDocument]) -> float:
    if not docs:
        return 0.0
    total = 0.0
    for doc in docs:
        s = 0.5
        if _CREDIBLE_PATTERNS.search(doc.text):  s += 0.2
        if _UNRELIABLE_PATTERNS.search(doc.text): s -= 0.3
        if _HEDGE_PATTERNS.search(doc.text):      s -= 0.05
        host = _host_of(doc.url)
        for edu in _EDUCATIONAL_HOSTS:
            if host == edu or host.endswith(f'.{edu}'):
                s += 0.15
                break
        total += max(0.0, min(1.0, s))
    return total / len(docs)


def _detect_narrative_bias(docs: list[LiveDocument]) -> list[str]:
    text = " ".join(d.text[:500] for d in docs)
    return [name for name, pat in _BIAS_MARKERS.items() if pat.search(text)]


class TruthFilter:
    """
    Ranks sentences from live web documents for relevance and credibility.
    Python port of Zophiel Engine retrieval-ranker.ts.
    """

    def rank(self, query: str, documents: list[LiveDocument],
             seed_urls: list[str] | None = None) -> TruthResult:
        live_docs = [d for d in documents if d.source == "live"]
        if not live_docs:
            return TruthResult(
                query=query, top_sentences=[], best_answer="No live documents available.",
                source_urls=[], credibility=0.0, narrative_bias=[], verdict="no_data",
            )

        seed_hosts = {_host_of(u) for u in (seed_urls or [])} - {''}
        kind, terms, raw_focus = self._parse_question(query)
        ranked: list[RankedSentence] = []

        for doc in live_docs:
            for sent in _split_sentences(doc.text):
                sc = _score_sentence(sent, terms, kind, doc, seed_hosts, raw_focus)
                if sc > 0:
                    ranked.append(RankedSentence(sentence=sent, url=doc.url, title=doc.title, score=sc))

        ranked.sort(key=lambda r: (-r.score, -len(r.sentence)))

        if kind == "definition":
            top = [r for r in ranked if _DEFINITION_SENTENCE.search(r.sentence) or _SUBJECT_FIRST.match(r.sentence)][:10]
        else:
            top = ranked[:10]

        best = top[0].sentence if top else "No relevant sentence found in live documents."
        cred = _credibility_score(live_docs)
        bias = _detect_narrative_bias(live_docs)
        verdict = "reliable" if cred >= 0.65 else ("mixed" if cred >= 0.35 else "unreliable")
        urls   = list(dict.fromkeys(r.url for r in top))

        return TruthResult(
            query=query,
            top_sentences=top,
            best_answer=best,
            source_urls=urls,
            credibility=cred,
            narrative_bias=bias,
            verdict=verdict,
            metadata={"doc_count": len(live_docs), "ranked_count": len(ranked), "kind": kind},
        )

    def _parse_question(self, query: str) -> tuple[str, list[str], str]:
        trimmed = query.strip()
        m = _DEFINITION_CUES.match(trimmed)
        if m:
            raw = m.group(1).rstrip('?').strip()
            return "definition", _tokenize(raw), raw
        return "general", _tokenize(trimmed), trimmed

    def quick_credibility(self, text: str) -> float:
        doc = LiveDocument(text=text, url="", title="", source="live")
        return _credibility_score([doc])

    def is_propaganda(self, text: str) -> bool:
        return bool(_UNRELIABLE_PATTERNS.search(text))


# ── Singleton ─────────────────────────────────────────────────────────────────
_filter = TruthFilter()

def rank(query: str, documents: list[LiveDocument], seed_urls: list[str] | None = None) -> TruthResult:
    return _filter.rank(query, documents, seed_urls)

def quick_credibility(text: str) -> float:
    return _filter.quick_credibility(text)

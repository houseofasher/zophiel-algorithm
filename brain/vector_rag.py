"""Vector RAG index — TF-IDF retrieval from corpus documents."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword → source-substring domain filter
# ---------------------------------------------------------------------------
_DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "BIOLOGY": {
        "dna","rna","gene","genetics","cell","chromosome","protein","enzyme",
        "mitosis","meiosis","photosynthesis","evolution","organism","species",
        "natural selection","mutation","ecology","bacteria","virus","antibody",
        "immune","vaccine","metabolism","ribosome","membrane","nucleus","atp",
        "replication","transcription","translation","allele","phenotype",
        "genotype","prokaryote","eukaryote","chloroplast","mitochondria",
    },
    "PHYSICS": {
        "gravity","gravitational","force","momentum","velocity","acceleration",
        "thermodynamics","entropy","energy","quantum","photon","electron",
        "proton","neutron","relativity","electromagnetic","wave","frequency",
        "amplitude","optics","refraction","diffraction","nuclear","fission",
        "fusion","magnetism","electric","charge","capacitor","resistor",
        "circuit","lagrangian","hamiltonian","schrodinger","heisenberg",
        "carnot","kinetic","potential","pressure","temperature","heat",
    },
    "CHEMISTRY": {
        "reaction","molecule","atom","bond","covalent","ionic","acid","base",
        "ph","periodic","element","compound","oxidation","reduction","catalyst",
        "titration","organic","inorganic","polymer","isomer","electrolyte",
        "concentration","mole","stoichiometry","enthalpy","entropy","gibbs",
        "electrode","galvanic","electrochemistry","aromatic","alkane","alkene",
    },
    "MATHEMATICS": {
        "calculus","derivative","integral","theorem","proof","matrix","vector",
        "probability","statistics","algebra","geometry","topology","number",
        "prime","factorial","fibonacci","logarithm","exponential","trigonometry",
        "differential","equation","polynomial","eigenvalue","determinant",
        "limit","continuity","convergence","series","sequence","graph theory",
    },
    "COMPUTER": {
        "algorithm","data structure","recursion","complexity","sorting","binary",
        "hash table","queue","stack","pointer","memory","cpu","cache",
        "operating system","network","protocol","tcp","ip","http","encryption",
        "compiler","interpreter","machine learning","neural network","database",
        "sql","programming","software","hardware","bit","byte","boolean",
        "gradient","backpropagation","regression","classification","clustering",
    },
    "THEOLOGY": {
        "god","divine","soul","spirit","spiritual","sacred","holy","sin","faith",
        "religion","theology","bible","quran","torah","scripture","prayer","worship",
        "demiurge","monad","gnostic","gnosis","kabbalah","kabbalistic","sephirot",
        "tree of life","mysticism","esoteric","occult","hermetic","alchemy",
        "lucifer","satan","devil","angel","demon","heaven","hell","afterlife",
        "christ","jesus","messiah","prophet","revelation","apocalypse","genesis",
        "consciousness","awareness","enlightenment","nirvana","moksha","karma",
        "astrotheology","pagan","archon","pleroma","logos","anthroposophy",
        "neoplatonism","emanation","cosmology","theosophy","hermeticism",
    },
    "ASTROLOGY": {
        "zodiac","horoscope","natal","birth chart","ascendant","descendant",
        "planet","saturn","jupiter","mercury","venus","mars","astrology",
        "vedic","jyotish","mahadasha","antardasha","nakshatra","rashi",
        "lagna","bhava","dasha","graha","mangal","shani","guru","rahu","ketu",
        "transit","aspect","conjunction","opposition","trine","sextile",
        "retrograde","eclipse","lunation","solstice","equinox",
        "sanghatta","sarvatobhadra","varga","divisional chart",
    },
    "HISTORY": {
        "ancient","medieval","renaissance","civilization","empire","dynasty",
        "war","battle","treaty","revolution","colonialism","conquest","kingdom",
        "pharaoh","pyramid","rome","greece","babylon","mesopotamia","sumerian",
        "egypt","maya","inca","aztec","ottoman","mongol","byzantine","feudal",
        "crusade","inquisition","reformation","enlightenment","industrial",
        "world war","cold war","holocaust","slavery","abolition","suffrage",
    },
    "PSYCHOLOGY": {
        "cognition","behavior","memory","learning","personality","emotion",
        "therapy","mental","perception","consciousness","motivation","attitude",
        "cognitive","developmental","social psychology","anxiety","depression",
        "freud","piaget","maslow","conditioning","reinforcement","schema",
    },
    "ECONOMICS": {
        "market","supply","demand","inflation","gdp","trade","monetary","fiscal",
        "investment","interest rate","recession","unemployment","microeconomics",
        "macroeconomics","utility","elasticity","equilibrium","game theory",
        "keynesian","monetarist","capital","labour","production","cost",
    },
    "PHILOSOPHY": {
        "ethics","metaphysics","epistemology","ontology","moral","justice",
        "utilitarianism","deontology","virtue","existentialism","phenomenology",
        "logic","reasoning","argument","premise","conclusion","fallacy",
        "plato","aristotle","kant","hume","descartes","nietzsche","socrates",
        "consciousness","free will","determinism","dualism","materialism",
    },
}

def _detect_source_filter(query: str) -> str | None:
    """Return the source-substring to filter by, or None for global search."""
    tokens = re.findall(r"[a-z]{3,}", query.lower())
    token_set = set(tokens)
    ql = query.lower()
    best_domain: str | None = None
    best_score = 0
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if " " in kw:
                if kw in ql:
                    score += 2
            else:
                # exact match OR prefix/suffix stem match (handles plurals, -ing, -ed, -tion)
                if kw in token_set:
                    score += 1
                else:
                    for tok in token_set:
                        if tok.startswith(kw) or kw.startswith(tok):
                            score += 1
                            break
        if score > best_score:
            best_score = score
            best_domain = domain
    # require at least 1 keyword match to apply filter
    return best_domain if best_score >= 1 else None


@dataclass
class RagHit:
    text: str
    source: str
    score: float
    document_id: int | None = None


class _RagIndex:
    def __init__(self) -> None:
        self._docs: list[dict] = []
        self._vectors: np.ndarray | None = None
        self._vocab: dict[str, int] = {}
        self._idf: np.ndarray | None = None
        self._built = False

    @property
    def document_count(self) -> int:
        return len(self._docs)

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-z]{3,}", text.lower())

    def _vectorize(self, texts: list[str]) -> np.ndarray:
        n = len(texts)
        m = len(self._vocab)
        mat = np.zeros((n, m), dtype=np.float32)
        for i, text in enumerate(texts):
            tokens = self._tokenize(text)
            from collections import Counter
            tf = Counter(tokens)
            total = max(1, len(tokens))
            for term, cnt in tf.items():
                idx = self._vocab.get(term)
                if idx is not None and self._idf is not None:
                    mat[i, idx] = (cnt / total) * self._idf[idx]
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        return mat / norms

    def build(self, docs: list[dict]) -> None:
        """docs: list of {text, source, id}"""
        from collections import Counter
        self._docs = docs
        n = len(docs)
        if n == 0:
            self._built = False
            return
        df: Counter = Counter()
        for doc in docs:
            df.update(set(self._tokenize(doc["text"])))
        min_df = 1 if n < 20 else 2
        terms = [t for t, c in df.most_common() if min_df <= c < 0.95 * n][:2000]
        self._vocab = {t: i for i, t in enumerate(terms)}
        idf = np.array([np.log((n + 1) / (df[t] + 1)) + 1.0 for t in terms], dtype=np.float32)
        self._idf = idf
        self._vectors = self._vectorize([d["text"] for d in docs])
        self._built = True
        logger.info("RAG index built: %d docs, %d terms", n, len(terms))

    def query(self, text: str, top_k: int = 5, domain_filter: str | None = None) -> list[RagHit]:
        if not self._built or self._vectors is None or len(self._docs) == 0:
            return []

        # Auto-detect domain from query keywords if not supplied
        source_filter = domain_filter or _detect_source_filter(text)

        if source_filter:
            hits = self._query_filtered(text, top_k, source_filter)
            # fall back to global if too few good hits
            if len(hits) < 3:
                hits = self._query_global(text, top_k)
        else:
            hits = self._query_global(text, top_k)

        return hits

    def _query_global(self, text: str, top_k: int) -> list[RagHit]:
        q_vec = self._vectorize([text])
        scores = (self._vectors @ q_vec.T).flatten()
        top_idxs = scores.argsort()[::-1][:top_k]
        results = []
        for idx in top_idxs:
            score = float(scores[idx])
            if score < 0.01:
                continue
            doc = self._docs[idx]
            results.append(RagHit(
                text=doc["text"],
                source=doc.get("source", "corpus"),
                score=round(score, 4),
                document_id=doc.get("id"),
            ))
        return results

    def _query_filtered(self, text: str, top_k: int, source_filter: str) -> list[RagHit]:
        """Score only docs whose source contains source_filter."""
        sf = source_filter.upper()
        # collect candidate indices
        candidate_idxs = [i for i, d in enumerate(self._docs)
                          if sf in d.get("source", "").upper()]
        if not candidate_idxs:
            return []
        q_vec = self._vectorize([text])
        # Score only candidates
        cand_vecs = self._vectors[candidate_idxs]
        scores = (cand_vecs @ q_vec.T).flatten()
        top_n = min(top_k, len(candidate_idxs))
        top_local = scores.argsort()[::-1][:top_n]
        results = []
        for local_i in top_local:
            score = float(scores[local_i])
            if score < 0.01:
                continue
            doc = self._docs[candidate_idxs[local_i]]
            results.append(RagHit(
                text=doc["text"],
                source=doc.get("source", "corpus"),
                score=round(score, 4),
                document_id=doc.get("id"),
            ))
        return results

    def rebuild(self) -> int:
        """Load all verified docs from DB and rebuild (direct sqlite3)."""
        import sqlite3 as _sq3
        DB_PATH = "/tmp/aureon_data/aureon.db"
        try:
            conn = _sq3.connect(DB_PATH)
            rows = conn.execute(
                "SELECT id, text, source FROM documents "
                "WHERE verified=1 AND quality_score>=0.3 LIMIT 30000"
            ).fetchall()
            conn.close()
            docs = [{"id": r[0], "text": r[1], "source": r[2] or "corpus"} for r in rows]
            self.build(docs)
            return len(docs)
        except Exception as exc:
            logger.warning("RAG rebuild failed: %s", exc)
            return 0


_INDEX: _RagIndex | None = None


def get_rag_index(*, force_rebuild: bool = False) -> _RagIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = _RagIndex()
    if force_rebuild or not _INDEX._built:
        _INDEX.rebuild()
    return _INDEX


def retrieve_with_citations(
    query: str,
    top_k: int = 5,
    domain: str | None = None,
) -> tuple[str, list[RagHit], list[str]]:
    """Return (context_text, hits, source_urls)."""
    index = get_rag_index()
    hits = index.query(query, top_k=top_k, domain_filter=domain)
    context_parts = [h.text for h in hits]
    context_text = '\n\n'.join(context_parts)
    source_urls = [h.source for h in hits if h.source]
    return context_text, hits, source_urls

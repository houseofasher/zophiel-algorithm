"""
LIVE SEARCH — Module 14 of the Zophiel Mind
Connects Zophiel Mind to live web search for current events and real-time answers.
Python port of Zophiel Engine search + retrieval pipeline.
Feeds results through TruthFilter for credibility scoring.
"""
from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchResult:
    query: str
    answer: str
    sources: list[dict]     # [{url, title, excerpt}]
    credibility: float
    narrative_bias: list[str]
    verdict: str
    needs_live: bool
    raw_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Search URL builders ───────────────────────────────────────────────────────

_SEARCH_ENGINES = {
    "ddg":           "https://html.duckduckgo.com/html/?q={q}",
    "bing":          "https://www.bing.com/search?q={q}",
    "brave":         "https://search.brave.com/search?q={q}",
    "wikipedia":     "https://en.wikipedia.org/wiki/Special:Search?search={q}",
    "britannica":    "https://www.britannica.com/search?query={q}",
}

_TEMPORAL_RE = re.compile(
    r'\b(today|yesterday|now|current|latest|recent|live|breaking|news|this week|this month|'
    r'2024|2025|2026|happening|ongoing|update)\b', re.I
)

_EDUCATIONAL_SEEDS = {
    "science":      ["https://arxiv.org", "https://nature.com", "https://sciencedirect.com"],
    "medicine":     ["https://pubmed.ncbi.nlm.nih.gov", "https://who.int", "https://mayoclinic.org"],
    "history":      ["https://worldhistory.org", "https://britannica.com", "https://wikipedia.org"],
    "economics":    ["https://imf.org", "https://worldbank.org", "https://investopedia.com"],
    "technology":   ["https://arxiv.org", "https://paperswithcode.com", "https://techcrunch.com"],
    "philosophy":   ["https://plato.stanford.edu", "https://iep.utm.edu", "https://wikipedia.org"],
    "occult":       ["https://sacred-texts.com", "https://thelemapedia.org", "https://esotericarchives.com"],
    "default":      ["https://en.wikipedia.org", "https://britannica.com"],
}


class LiveSearch:
    """
    Fetches live web results for current-event queries.
    Uses urllib (stdlib only) — no external dependencies required.
    Passes results through TruthFilter for credibility scoring.
    """

    def __init__(self):
        self._session_cache: dict[str, SearchResult] = {}

    def search(self, query: str, domain_hint: str = "default",
               max_results: int = 5) -> SearchResult:
        """
        Main entry point. Fetches live results for a query.
        Returns a SearchResult with credibility scoring.
        """
        from brain.mind.truth_filter import TruthFilter, LiveDocument

        needs_live = self._needs_live(query)
        cache_key  = f"{query}:{domain_hint}"

        if cache_key in self._session_cache:
            return self._session_cache[cache_key]

        # Build seed URLs for this query + domain
        seeds    = self._build_seeds(query, domain_hint)
        raw_docs = []

        if needs_live:
            raw_docs = self._fetch_pages(seeds, query, max_results)

        if not raw_docs:
            # Offline fallback — construct answer from query structure alone
            result = self._offline_result(query)
            self._session_cache[cache_key] = result
            return result

        tf     = TruthFilter()
        truth  = tf.rank(query, raw_docs, seed_urls=seeds)

        sources = [
            {"url": r.url, "title": r.title, "excerpt": r.sentence[:240]}
            for r in truth.top_sentences[:max_results]
        ]

        result = SearchResult(
            query=query,
            answer=truth.best_answer,
            sources=sources,
            credibility=truth.credibility,
            narrative_bias=truth.narrative_bias,
            verdict=truth.verdict,
            needs_live=needs_live,
            raw_count=len(raw_docs),
            metadata={
                "seeds": seeds[:3],
                "domain_hint": domain_hint,
                "ranked": len(truth.top_sentences),
            },
        )
        self._session_cache[cache_key] = result
        return result

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _needs_live(self, query: str) -> bool:
        return bool(_TEMPORAL_RE.search(query))

    def _build_seeds(self, query: str, domain: str) -> list[str]:
        base_seeds = _EDUCATIONAL_SEEDS.get(domain, _EDUCATIONAL_SEEDS["default"])
        q_enc = urllib.parse.quote_plus(query)
        expanded = list(base_seeds)

        # Add site-search URLs (mirroring augmentSeedsForQuestion from retrieval-ranker.ts)
        for seed in base_seeds:
            try:
                host = urllib.parse.urlparse(seed).hostname or ""
                host = host.replace("www.", "").lower()
                if "arxiv.org" in host:
                    expanded.append(f"https://arxiv.org/search/?query={q_enc}&searchtype=all")
                elif "britannica.com" in host:
                    expanded.append(f"https://www.britannica.com/search?query={q_enc}")
                elif "wikipedia.org" in host:
                    expanded.append(f"https://en.wikipedia.org/wiki/Special:Search?search={q_enc}")
                elif "pubmed" in host:
                    expanded.append(f"https://pubmed.ncbi.nlm.nih.gov/?term={q_enc}")
            except Exception:
                pass

        return list(dict.fromkeys(expanded))[:6]

    def _fetch_pages(self, urls: list[str], query: str,
                     max_pages: int) -> list:
        """
        Fetch pages using stdlib urllib. Returns LiveDocument list.
        Falls back gracefully if network is unavailable.
        """
        from brain.mind.truth_filter import LiveDocument
        import urllib.request
        import html
        import time

        docs = []
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; ZophielBot/1.0; +https://zophiel.ai)"
            ),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }

        for url in urls[:max_pages]:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    raw_html = resp.read().decode('utf-8', errors='replace')
                text = self._extract_text(raw_html)
                title = self._extract_title(raw_html)
                if len(text) >= 100:
                    docs.append(LiveDocument(
                        text=text[:8000],
                        url=url,
                        title=title,
                        source="live",
                    ))
                time.sleep(0.3)   # polite crawl
            except Exception:
                continue

        return docs

    def _extract_text(self, html_str: str) -> str:
        """Strip HTML tags and extract readable text."""
        import html as html_mod
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_str, flags=re.S | re.I)
        text = re.sub(r'<style[^>]*>.*?</style>',  '', text,     flags=re.S | re.I)
        text = re.sub(r'<[^>]+>',                  ' ', text)
        text = html_mod.unescape(text)
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()

    def _extract_title(self, html_str: str) -> str:
        m = re.search(r'<title[^>]*>(.*?)</title>', html_str, re.I | re.S)
        if m:
            import html as html_mod
            return html_mod.unescape(m.group(1).strip())[:200]
        return "Unknown"

    def _offline_result(self, query: str) -> SearchResult:
        """Return a honest offline fallback."""
        return SearchResult(
            query=query,
            answer=(
                f"Live search is unavailable or not required for this query. "
                f"Zophiel's internal corpus will be used to answer questions about '{query}'."
            ),
            sources=[],
            credibility=0.0,
            narrative_bias=[],
            verdict="no_data",
            needs_live=self._needs_live(query),
            raw_count=0,
        )

    def augment_seeds(self, seeds: list[str], query: str) -> list[str]:
        """Expand seed URLs with site-specific search URLs (port of augmentSeedsForQuestion)."""
        return self._build_seeds(query, "default") + seeds


# ── Singleton ─────────────────────────────────────────────────────────────────
_searcher = LiveSearch()

def search(query: str, domain_hint: str = "default", max_results: int = 5) -> SearchResult:
    return _searcher.search(query, domain_hint, max_results)

def needs_live(query: str) -> bool:
    return _searcher._needs_live(query)

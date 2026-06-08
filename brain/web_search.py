"""Web search bridge — optionally queries external search for live knowledge."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def web_search_enabled() -> bool:
    return os.environ.get("AUREON_WEB_SEARCH", "0") == "1"


def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Perform a web search. Returns empty list if disabled or unavailable."""
    if not web_search_enabled():
        return []
    try:
        import httpx
        # DuckDuckGo instant answers (no API key required)
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}
        resp = httpx.get(url, params=params, timeout=8.0)
        data = resp.json()
        results: list[dict] = []
        abstract = data.get("AbstractText", "")
        if abstract:
            results.append({
                "text": abstract,
                "source": data.get("AbstractURL", "duckduckgo"),
                "title": data.get("Heading", query),
            })
        for topic in data.get("RelatedTopics", [])[:max_results - 1]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "text": topic["Text"],
                    "source": topic.get("FirstURL", "duckduckgo"),
                    "title": topic.get("Text", "")[:60],
                })
        return results
    except Exception as exc:
        logger.debug("Web search failed: %s", exc)
        return []

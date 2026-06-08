#!/usr/bin/env python3
"""
brain/web_extractor.py
Fetches a URL, strips HTML to clean sentences, scores them against a query
using TF-IDF cosine similarity, and returns a temporary in-memory _RagIndex
that can be merged with the corpus at answer time.
"""
import re
import urllib.request
import urllib.error
from html.parser import HTMLParser
from brain.vector_rag import _RagIndex, RagHit

# ── HTML stripper ──────────────────────────────────────────────────────────────
_SKIP_TAGS = {
    'script', 'style', 'noscript', 'nav', 'header', 'footer',
    'aside', 'form', 'button', 'svg', 'figure', 'figcaption',
}

class _Stripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._buf = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._buf.append(data)

    def get_text(self):
        return ' '.join(self._buf)


def _html_to_text(html: str) -> str:
    s = _Stripper()
    try:
        s.feed(html)
    except Exception:
        pass
    text = s.get_text()
    # Collapse whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── Sentence chunker ───────────────────────────────────────────────────────────
_SENT_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')

def _chunk_sentences(text: str, min_len: int = 40, max_len: int = 500) -> list[str]:
    """Split text into sentences, merge fragments shorter than min_len."""
    raw = _SENT_RE.split(text)
    out = []
    buf = ''
    for sent in raw:
        sent = sent.strip()
        if not sent:
            continue
        buf = (buf + ' ' + sent).strip() if buf else sent
        if len(buf) >= min_len:
            if len(buf) <= max_len:
                out.append(buf)
            else:
                # Split long chunk by newlines or commas
                for part in re.split(r'[;\n]', buf):
                    part = part.strip()
                    if len(part) >= min_len:
                        out.append(part[:max_len])
            buf = ''
    if buf and len(buf) >= min_len:
        out.append(buf[:max_len])
    return out


# ── URL fetcher ────────────────────────────────────────────────────────────────
_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.9',
}

def fetch_url(url: str, timeout: int = 10) -> str:
    """Fetch a URL and return plain text. Returns '' on failure."""
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(500_000)          # max 500 KB
            charset = 'utf-8'
            ct = resp.headers.get_content_charset()
            if ct:
                charset = ct
            html = raw.decode(charset, errors='replace')
        return _html_to_text(html)
    except Exception as e:
        return ''


# ── Main API ───────────────────────────────────────────────────────────────────
def build_web_index(url: str, query: str, top_k: int = 10) -> _RagIndex:
    """
    Fetch *url*, chunk to sentences, score against *query*, keep top_k,
    and return a temporary in-memory _RagIndex ready for .query().
    Returns an empty index on failure.
    """
    text = fetch_url(url)
    if not text:
        idx = _RagIndex()
        idx.build([])
        return idx

    sentences = _chunk_sentences(text)
    if not sentences:
        idx = _RagIndex()
        idx.build([])
        return idx

    # Pre-score against query to keep only relevant sentences
    # We build a tiny temp index, query it, then build the real one from top hits
    docs = [{'id': i, 'text': s, 'source': url} for i, s in enumerate(sentences)]
    pre = _RagIndex()
    pre.build(docs)
    hits = pre.query(query, top_k=min(top_k * 3, len(docs)))
    keep = [{'id': i, 'text': h.text, 'source': url}
            for i, h in enumerate(hits) if h.score > 0.05]

    idx = _RagIndex()
    idx.build(keep)
    return idx


def extract_and_retrieve(url: str, query: str, top_k: int = 5) -> list[RagHit]:
    """
    Convenience wrapper: fetch url, build temp index, return top_k hits.
    """
    idx = build_web_index(url, query, top_k=top_k)
    return idx.query(query, top_k=top_k)


if __name__ == '__main__':
    # Quick smoke-test
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://en.wikipedia.org/wiki/Entropy'
    q   = sys.argv[2] if len(sys.argv) > 2 else 'What is entropy?'
    hits = extract_and_retrieve(url, q, top_k=3)
    print(f"Top hits for '{q}' from {url}:")
    for h in hits:
        print(f"  [{h.score:.3f}] {h.text[:120]}")

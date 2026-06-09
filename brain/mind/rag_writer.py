"""
rag_writer.py — The "writer" half of retrieval-augmented generation.
=====================================================================
THE HONEST STORY THIS MODULE TELLS
----------------------------------
Zophiel's retrieval engine is a librarian: it finds the passages whose words best
match your question and reads them back, lightly stitched. That is competent
*finding*, not *writing* — which is why the raw answers can read like quotes.

This module is the optional second half: the writer. When (and only when) a real
language model is configured via environment variables, the librarian's retrieved
facts are handed to that model with a strict instruction — "use ONLY these facts,
write an original answer in your own words, and if they do not answer the question
say so." The LLM does the composing; the corpus keeps it factual and grounded.

This is retrieval-augmented generation done properly, with a hard wall:
  - The model is given the retrieved facts and nothing else as ground truth.
  - It is told not to invent beyond them.
  - If no key is configured, this module does nothing and the deterministic
    retrieval answer is used unchanged. Non-LLM behavior is the default.

No third-party dependencies — uses urllib so it works anywhere the rest of the
engine runs. Supports OpenAI-compatible chat APIs and the Anthropic Messages API.

Configuration (all optional; absence => disabled, pure retrieval):
  ZOPHIEL_LLM_API_KEY   the API key for the writer model
  ZOPHIEL_LLM_PROVIDER  "openai" (default, OpenAI-compatible) or "anthropic"
  ZOPHIEL_LLM_MODEL     model id (sensible default per provider)
  ZOPHIEL_LLM_BASE_URL  override base URL (for OpenAI-compatible gateways)
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error

_TIMEOUT = float(os.environ.get("ZOPHIEL_LLM_TIMEOUT", "20"))


def _cfg() -> dict | None:
    key = os.environ.get("ZOPHIEL_LLM_API_KEY", "").strip()
    if not key:
        return None
    provider = os.environ.get("ZOPHIEL_LLM_PROVIDER", "openai").strip().lower()
    if provider == "anthropic":
        return {
            "provider": "anthropic",
            "key": key,
            "model": os.environ.get("ZOPHIEL_LLM_MODEL", "claude-3-5-haiku-latest"),
            "base": os.environ.get("ZOPHIEL_LLM_BASE_URL", "https://api.anthropic.com"),
        }
    return {
        "provider": "openai",
        "key": key,
        "model": os.environ.get("ZOPHIEL_LLM_MODEL", "gpt-4o-mini"),
        "base": os.environ.get("ZOPHIEL_LLM_BASE_URL", "https://api.openai.com"),
    }


def llm_available() -> bool:
    """True only when a writer model is actually configured."""
    return _cfg() is not None


_SYSTEM = (
    "You are the synthesis voice of Zophiel, a retrieval-grounded AI. "
    "You will be given a user question and a short list of FACTS retrieved from a "
    "curated corpus. Write a single, clear, original answer in your own words, "
    "grounded ONLY in those facts. Do not add information beyond them and do not "
    "invent specifics. If the facts do not actually answer the question, say plainly "
    "that you don't have confident data on it. Be direct and natural — no preamble, "
    "no 'based on the facts', no bullet lists unless the question demands them."
)


def _build_prompt(query: str, facts: list[str]) -> str:
    numbered = "\n".join(f"- {f}" for f in facts if f and f.strip())
    return (
        f"QUESTION:\n{query}\n\n"
        f"FACTS (your only ground truth):\n{numbered or '(none retrieved)'}\n\n"
        f"Write the grounded answer now."
    )


def _post(url: str, headers: dict, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _call_openai(cfg: dict, query: str, facts: list[str]) -> str:
    body = _post(
        f"{cfg['base'].rstrip('/')}/v1/chat/completions",
        {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"},
        {
            "model": cfg["model"],
            "temperature": 0.3,
            "max_tokens": 400,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _build_prompt(query, facts)},
            ],
        },
    )
    return body["choices"][0]["message"]["content"].strip()


def _call_anthropic(cfg: dict, query: str, facts: list[str]) -> str:
    body = _post(
        f"{cfg['base'].rstrip('/')}/v1/messages",
        {
            "x-api-key": cfg["key"],
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        {
            "model": cfg["model"],
            "max_tokens": 400,
            "temperature": 0.3,
            "system": _SYSTEM,
            "messages": [{"role": "user", "content": _build_prompt(query, facts)}],
        },
    )
    # Anthropic returns a list of content blocks.
    parts = body.get("content", [])
    return "".join(p.get("text", "") for p in parts).strip()


def write_answer(query: str, facts: list[str], fallback: str) -> tuple[str, str]:
    """Generate a grounded, original answer from retrieved facts.

    Returns (text, method). method is:
      "rag+llm(<provider>)" when the writer model composed the answer,
      "rag+synthesize"      when no model is configured or the call failed
                            (the deterministic retrieval answer is returned).

    The librarian always has a fallback; the writer only ever improves on it.
    """
    cfg = _cfg()
    if cfg is None or not facts:
        return fallback, "rag+synthesize"
    try:
        if cfg["provider"] == "anthropic":
            text = _call_anthropic(cfg, query, facts)
        else:
            text = _call_openai(cfg, query, facts)
        if text:
            return text, f"rag+llm({cfg['provider']})"
    except (urllib.error.URLError, KeyError, ValueError, TimeoutError, OSError) as e:
        # Fail safe: never let a writer outage break the answer. Fall back to the
        # grounded retrieval synthesis and surface the reason in the method tag.
        print(f"[rag_writer] writer unavailable, using retrieval fallback: {e}")
    return fallback, "rag+synthesize"

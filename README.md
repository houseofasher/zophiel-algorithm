# Zophiel / SOLIA — AI Engine

Custom non-LLM AI system built by Aureon Software.

## Architecture

```
Query
  → Fast-Path (math / constants)
  → Asher Logic Decode (3-layer: surface / mechanism / truth)
  → TF-IDF RAG (29,741-doc SQLite corpus)
  → Humanlike Synthesizer
  → Response
```

**Components:**
- `brain/` — 90+ modules: cortex, vector RAG, 22 mind modules, 6 brain regions, vision
- `cyber_defence.py` — Nomad cyber defence (STRIDE, PQC, Sovereign Organism)
- `cyber/` — Nomad Cyber Algorithm (TypeScript: Kyber1024, Dilithium5, Imperial stack)
- `data/` — corpus_knowledge.json (54 domains), aureon.db (29,741 docs), training dataset
- `app.py` — Flask REST API (Railway entry point)

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

## API

```
POST /ask       { "query": "How does quantum entanglement work?" }
GET  /health    { "status": "ok", "docs": 29741 }
```

## Zophiel live search

```bash
AUREON_WEB_SEARCH=1 python app.py
```

## Deploy to Railway

1. Push this repo to GitHub
2. Connect repo in Railway → New Project → Deploy from GitHub
3. Railway auto-detects `railway.toml` and runs `python app.py`
4. Optional: set `AUREON_WEB_SEARCH=1` in Railway environment variables

## Test the full pipeline

```bash
python full_domain_test.py
# Expected: 60/60 questions synthesised across 6 domains
```

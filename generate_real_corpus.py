#!/usr/bin/env python3
"""
Real-content corpus generator for Aureon/SOLIA — FIXED VERSION.

Fixes vs original:
  1. Paths are configurable (no hardcoded session paths)
  2. Templates no longer produce "is a concept within" / "operates as follows" boilerplate
  3. Raw facts are inserted ONCE per domain, not repeated across all 10 doc_types
  4. Each doc_type picks a different fact slice so answers vary
  5. Works standalone — no full web app needed

Usage:
    python generate_real_corpus.py
    python generate_real_corpus.py --db /path/to/aureon.db --knowledge /path/to/corpus_knowledge.json
"""
import sqlite3, re, time, json, argparse
from pathlib import Path

# ── Default paths (relative to this script) ──────────────────────────────────
_HERE = Path(__file__).resolve().parent
DEFAULT_DB = str(_HERE / "aureon.db")
DEFAULT_KNOWLEDGE = str(_HERE / "corpus_knowledge.json")
DEFAULT_TAXONOMY = None   # optional; set to path of COMPLETE_HUMAN_DOMAIN_TAXONOMY.txt

# ── Document generation ───────────────────────────────────────────────────────
DOC_TYPES = [
    "definition", "mechanism", "principles", "applications",
    "examples", "history", "connections", "methods",
    "challenges", "implications",
]

def make_doc(topic, subdomain, domain, doc_type, facts):
    """Generate a natural-language document. Facts are real sentences from corpus_knowledge.json."""
    n = len(facts)
    # Each doc_type starts from a different offset so content doesn't repeat
    offset = DOC_TYPES.index(doc_type)
    start = (abs(hash(topic)) + offset * 3) % max(n, 1)
    f = facts[start:] + facts[:start]

    # Use facts directly — no "is a concept within" style wrappers
    f0 = f[0]
    f1 = f[1] if n > 1 else f[0]
    f2 = f[2] if n > 2 else f[0]
    f3 = f[3] if n > 3 else f[0]
    f4 = f[4] if n > 4 else f[0]

    if doc_type == "definition":
        return f"{topic} — {f0} {f1}"
    elif doc_type == "mechanism":
        return f"{topic}: {f0} {f2}"
    elif doc_type == "principles":
        return f"{topic} key principles: {f0} {f1}"
    elif doc_type == "applications":
        return f"{topic} applications: {f0} {f3}"
    elif doc_type == "examples":
        return f"{topic} examples: {f1} {f4}"
    elif doc_type == "history":
        return f"{topic} history: {f0} {f2}"
    elif doc_type == "connections":
        return f"{topic} in {subdomain}: {f0} {f1}"
    elif doc_type == "methods":
        return f"{topic} methods: {f0} {f2}"
    elif doc_type == "challenges":
        return f"{topic} challenges: {f0} {f3}"
    elif doc_type == "implications":
        return f"{topic} implications: {f0} {f1}"
    return f"{topic}: {f0}"


# ── Fact lookup ───────────────────────────────────────────────────────────────
def build_keyword_index(knowledge):
    return {k: set(k.upper().replace('&','').replace(',','').split()) for k in knowledge}

def get_facts_for(domain_name, subdomain_name, knowledge, kw_index):
    sub_up = subdomain_name.upper().replace('&','').replace(',','').replace('(','').replace(')','')
    # Exact match
    for key in knowledge:
        if key.upper() == sub_up:
            return knowledge[key]
    # Substring match
    for key in knowledge:
        if key.upper() in sub_up or sub_up in key.upper():
            return knowledge[key]
    # Keyword overlap
    s_words = set(sub_up.split()) - {'AND','OF','THE','IN','FOR','TO','A','SCIENCES','SCIENCE'}
    best_key, best_score = None, 0
    for key, kw in kw_index.items():
        score = len(s_words & kw)
        if score > best_score:
            best_score, best_key = score, key
    if best_key and best_score > 0:
        return knowledge[best_key]
    # Domain fallback
    d_up = domain_name.upper().replace('&','').replace(',','').replace('(','').replace(')','')
    d_words = set(d_up.split()) - {'AND','OF','THE','IN','FOR','TO','A','SCIENCES','SCIENCE'}
    for key, kw in kw_index.items():
        score = len(d_words & kw)
        if score > best_score:
            best_score, best_key = score, key
    if best_key and best_score > 0:
        return knowledge[best_key]
    # Static mapping
    domain_to_key = {
        'SCIENCE': 'PHYSICS', 'MEDICINE': 'CLINICAL MEDICINE', 'TECHNOLOGY': 'COMPUTER SCIENCE',
        'ENGINEERING': 'MECHANICAL ENGINEERING', 'PHILOSOPHY': 'METAPHYSICS',
        'RELIGION': 'ABRAHAMIC RELIGIONS', 'ARTS': 'ARTS & CREATIVE EXPRESSION',
        'HUMANITIES': 'HUMANITIES', 'SOCIAL': 'SOCIAL SCIENCES', 'LAW': 'LAW & JURISPRUDENCE',
        'ECONOMICS': 'ECONOMICS & BUSINESS', 'EDUCATION': 'EDUCATION',
        'MILITARY': 'MILITARY & WARFARE', 'AGRICULTURE': 'AGRICULTURE & FOOD SYSTEMS',
        'ENVIRONMENTAL': 'ENVIRONMENTAL SCIENCE & SUSTAINABILITY',
        'COMMUNICATION': 'COMMUNICATION & MEDIA', 'SPORTS': 'SPORTS & PHYSICAL CULTURE',
        'GOVERNANCE': 'GOVERNANCE & POLITICAL SYSTEMS',
        'PSYCHOLOGY': 'PSYCHOLOGY OF HUMAN EXPERIENCE',
        'CRAFT': 'CRAFT & TRADITIONAL SKILLS',
        'TRANSPORTATION': 'TRANSPORTATION & LOGISTICS', 'ENERGY': 'ENERGY SYSTEMS',
        'COGNITIVE': 'COGNITIVE & BEHAVIORAL SCIENCES', 'SPACE': 'SPACE EXPLORATION & ASTRONAUTICS',
        'INFORMATION': 'INFORMATION & KNOWLEDGE SYSTEMS',
        'ETHICS': 'ETHICS, RIGHTS & JUSTICE SYSTEMS', 'SURVIVAL': 'SURVIVAL, PRIMAL & ANCESTRAL SKILLS',
        'CYBER': 'COMPUTER SCIENCE', 'SECURITY': 'COMPUTER SCIENCE',
    }
    for kw, mapped in domain_to_key.items():
        if kw in domain_name.upper() and mapped in knowledge:
            return knowledge[mapped]
    return knowledge[list(knowledge.keys())[abs(hash(domain_name)) % len(knowledge)]]


# ── Taxonomy parser ───────────────────────────────────────────────────────────
def parse_taxonomy(path):
    nodes = []
    current_domain_id, current_domain = None, None
    current_sub_id, current_sub = None, None
    current_micro_id = None
    for line in open(path):
        s = line.strip()
        m = re.match(r'\[DOMAIN (\d+)\] (.+)', s)
        if m:
            current_domain_id = int(m.group(1))
            current_domain = m.group(2).strip()
            current_sub_id = current_sub = current_micro_id = None
            continue
        m = re.match(r'(\d{2})\.(\d{2}) (.+)', s)
        if m and current_domain_id:
            current_sub_id = int(m.group(2))
            current_sub = m.group(3).strip()
            current_micro_id = None
            nodes.append((current_domain_id, current_sub_id, None, current_domain, current_sub, current_sub))
            continue
        m = re.match(r'(\d{2})\.(\d{2})\.(\d{2}) (.+)', s)
        if m and current_sub_id is not None:
            current_micro_id = int(m.group(3))
            nodes.append((current_domain_id, current_sub_id, current_micro_id, current_domain, current_sub, m.group(4).strip()))
            continue
        m = re.match(r'- (.+)', s)
        if m and current_sub_id is not None:
            nodes.append((current_domain_id, current_sub_id, current_micro_id, current_domain, current_sub, m.group(1).strip()))
    return nodes


def knowledge_only_nodes(knowledge):
    """Fallback: generate nodes directly from knowledge domains when no taxonomy file."""
    nodes = []
    for i, domain in enumerate(knowledge.keys(), 1):
        nodes.append((i, 1, None, domain, domain, domain))
    return nodes


# ── DB setup ──────────────────────────────────────────────────────────────────
def ensure_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_id INTEGER,
            subdomain_id INTEGER,
            micro_subdomain_id INTEGER,
            source TEXT,
            text TEXT,
            quality_score REAL DEFAULT 0.85,
            verified INTEGER DEFAULT 1,
            created_at TEXT DEFAULT '2025-01-01 00:00:00'
        )
    """)
    conn.commit()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Aureon real corpus generator")
    parser.add_argument('--db', default=DEFAULT_DB, help='SQLite DB path')
    parser.add_argument('--knowledge', default=DEFAULT_KNOWLEDGE, help='corpus_knowledge.json path')
    parser.add_argument('--taxonomy', default=DEFAULT_TAXONOMY, help='COMPLETE_HUMAN_DOMAIN_TAXONOMY.txt path')
    args = parser.parse_args()

    print(f"DB:        {args.db}")
    print(f"Knowledge: {args.knowledge}")

    print("\nLoading knowledge...")
    with open(args.knowledge) as f:
        knowledge = json.load(f)
    kw_index = build_keyword_index(knowledge)
    print(f"  {len(knowledge)} domains loaded.")

    if args.taxonomy and Path(args.taxonomy).exists():
        print("Parsing taxonomy...")
        nodes = parse_taxonomy(args.taxonomy)
        print(f"  {len(nodes)} nodes found.")
    else:
        print("No taxonomy file — using knowledge domains directly.")
        nodes = knowledge_only_nodes(knowledge)
        print(f"  {len(nodes)} nodes.")

    import os
    os.makedirs(Path(args.db).parent, exist_ok=True)
    conn = sqlite3.connect(args.db)
    ensure_db(conn)
    cur = conn.cursor()

    print("\nClearing old documents...")
    cur.execute("DELETE FROM documents")
    conn.commit()

    print("Generating documents...")
    batch = []
    total = 0
    t0 = time.time()
    seen_raw_facts = set()   # dedup: insert each raw fact only once per source

    for domain_id, sub_id, micro_id, domain_name, sub_name, topic in nodes:
        facts = get_facts_for(domain_name, sub_name, knowledge, kw_index)
        source = f"{domain_name}/{sub_name}"

        # 1. Generated doc per doc_type (varied, non-repetitive)
        for doc_type in DOC_TYPES:
            text = make_doc(topic, sub_name, domain_name, doc_type, facts)
            batch.append((domain_id, sub_id, micro_id, source, text, 0.85, 1))
            total += 1

        # 2. Raw facts inserted ONCE per unique (source, fact) pair
        for fact in facts:
            key = (source, fact)
            if key not in seen_raw_facts:
                seen_raw_facts.add(key)
                batch.append((domain_id, sub_id, micro_id, source, fact, 0.95, 1))
                total += 1

        if len(batch) >= 1000:
            cur.executemany(
                "INSERT INTO documents (domain_id, subdomain_id, micro_subdomain_id, source, text, quality_score, verified) VALUES (?,?,?,?,?,?,?)",
                batch
            )
            conn.commit()
            batch = []
            print(f"  {total:,} docs ... ({time.time()-t0:.1f}s)")

    if batch:
        cur.executemany(
            "INSERT INTO documents (domain_id, subdomain_id, micro_subdomain_id, source, text, quality_score, verified) VALUES (?,?,?,?,?,?,?)",
            batch
        )
        conn.commit()

    final = cur.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    conn.close()
    print(f"\nDone! {final:,} documents in {time.time()-t0:.1f}s -> {args.db}")


if __name__ == "__main__":
    main()

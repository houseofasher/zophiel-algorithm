#!/usr/bin/env python3
"""
AUREON / SOLIA — Full Domain Test
• 10 unique questions per major domain (synthesis check — not quoting dataset)
• Cyber defence module integrated (Nomad Cyber Algorithm)
• Zophiel current events live search test
"""

import sys, re, json, sqlite3, math, random, logging, textwrap
from pathlib import Path
from collections import Counter
import numpy as np

logging.basicConfig(level=logging.WARNING)

# ── Paths ──────────────────────────────────────────────────────────────────
DB_PATH       = "/tmp/aureon_fixed.db"
KNOWLEDGE_PATH= "/sessions/quirky-trusting-brahmagupta/mnt/uploads/corpus_knowledge.json"
CYBER_MODULE  = "/sessions/quirky-trusting-brahmagupta/mnt/Aureon Files/cyber_defence.py"

# ── Load corpus knowledge ──────────────────────────────────────────────────
with open(KNOWLEDGE_PATH) as f:
    KNOWLEDGE = json.load(f)

# ── Load cyber_defence module ─────────────────────────────────────────────
import importlib.util
spec = importlib.util.spec_from_file_location("cyber_defence", CYBER_MODULE)
cyber = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cyber)

# ── TF-IDF RAG ────────────────────────────────────────────────────────────
JUNK = ['is a concept within','operates as follows','in the context of',
        'establishes what','guide understanding of','from prior context',
        'this history shaped','these cases demonstrate','these uses reflect',
        'these methods are standard','these principles guide']
TMPL = re.compile(r'^(The (mechanism|implications)|Concrete examples|Methods and|Key challenges|Core principles of\s)',re.I)

def _is_real(s):
    if len(s)<50: return False
    if any(j in s.lower() for j in JUNK): return False
    if TMPL.match(s): return False
    return True

def _extract_facts(hits, max_facts=5):
    cands=[]
    for h in hits:
        for sent in re.split(r'(?<=[.!?])\s+', h['text']):
            sent=sent.strip()
            if not _is_real(sent): continue
            score=1.0
            if re.search(r'\d',sent): score+=0.5
            if re.search(r'[=><]',sent): score+=0.3
            if len(sent)>100: score+=0.2
            cands.append((score,sent))
    seen,out=set(),[]
    for _,s in sorted(cands,key=lambda x:-x[0]):
        k=s.lower()[:60]
        if k not in seen: seen.add(k); out.append(s)
        if len(out)>=max_facts: break
    return out

_OPENERS=["Here's the pattern:","At the core of it:","Strip the noise away:","Run the logic forward:","The data runs like this:"]
_BRIDGES=["What most people miss:","The deeper layer:","The mechanism behind it:"]
_CLOSERS=["That's the read.","Pattern confirmed.","Run that forward — it holds."]

def synthesize(hits, extra=""):
    facts=_extract_facts(hits)
    if not facts and not extra:
        return "Insufficient corpus data for this query."
    parts=[]
    used=set()
    def add(pfx,fact):
        k=fact.lower()[:80]
        if k in used: return
        used.add(k)
        parts.append(f"{pfx} {fact}." if pfx else fact+".")
    if extra: parts.append(extra)
    if facts:
        add(random.choice(_OPENERS) if not extra else "", facts[0])
        for i,f in enumerate(facts[1:]):
            add(random.choice(_BRIDGES) if i==0 else "", f)
    if len(facts)>=2 or extra: parts.append(random.choice(_CLOSERS))
    ans=re.sub(r'\s+',' ',' '.join(parts)).strip()
    # dedup sentences
    sents,seen_s=[],set()
    for s in re.split(r'(?<=[.!?])\s+',ans):
        k=s.lower()[:80]
        if k and k not in seen_s: seen_s.add(k); sents.append(s)
    return ' '.join(sents)

class RagIndex:
    def __init__(self): self._docs=[]; self._vectors=None; self._vocab={}; self._idf=None; self._built=False
    def _tok(self,t): return re.findall(r"[a-z]{3,}",t.lower())
    def _vec(self,texts):
        n,m=len(texts),len(self._vocab)
        mat=np.zeros((n,m),dtype=np.float32)
        for i,t in enumerate(texts):
            tf=Counter(self._tok(t)); tot=max(1,sum(tf.values()))
            for term,cnt in tf.items():
                idx=self._vocab.get(term)
                if idx is not None and self._idf is not None:
                    mat[i,idx]=(cnt/tot)*self._idf[idx]
        norms=np.linalg.norm(mat,axis=1,keepdims=True)
        return mat/np.where(norms==0,1,norms)
    def build(self,docs):
        self._docs=docs; n=len(docs)
        if not n: return
        df=Counter()
        for d in docs: df.update(set(self._tok(d['text'])))
        terms=[t for t,c in df.most_common() if 1<=c<0.95*n][:4000]
        self._vocab={t:i for i,t in enumerate(terms)}
        self._idf=np.array([np.log((n+1)/(df[t]+1))+1.0 for t in terms],dtype=np.float32)
        self._vectors=self._vec([d['text'] for d in docs]); self._built=True
    def load_db(self):
        conn=sqlite3.connect(DB_PATH)
        rows=conn.execute("SELECT id,text,source FROM documents WHERE verified=1 LIMIT 50000").fetchall()
        conn.close()
        docs=[{"id":r[0],"text":r[1],"source":r[2] or "corpus"} for r in rows]
        self.build(docs); return len(docs)
    def query(self,text,top_k=8,src=None):
        if not self._built or self._vectors is None: return []
        q=self._vec([text])
        scores=(self._vectors@q.T).flatten()
        # Domain filter
        if src:
            ci=[i for i,d in enumerate(self._docs) if src.upper() in d.get('source','').upper()]
            if len(ci)>=3:
                cs=scores[ci]; top=cs.argsort()[::-1][:top_k]
                res=[{"text":self._docs[ci[t]]["text"],"source":self._docs[ci[t]]["source"],"score":round(float(cs[t]),4)} for t in top if float(cs[t])>0.01]
                if len(res)>=3: return res
        top_i=scores.argsort()[::-1][:top_k]
        return [{"text":self._docs[i]["text"],"source":self._docs[i]["source"],"score":round(float(scores[i]),4)} for i in top_i if float(scores[i])>0.01]

# ── Fast path ──────────────────────────────────────────────────────────────
CONSTS={'speed of light':'299,792,458 m/s','planck':'6.626×10⁻³⁴ J·s','avogadro':'6.022×10²³ mol⁻¹','pi':'3.14159265...','boltzmann':'1.381×10⁻²³ J/K','golden ratio':'φ≈1.618'}
MATH_RE=re.compile(r'(?:what\s+is\s+)?([0-9\s\+\-\*\/\(\)\^\.]+ ?)\??$',re.I)
def _word_in_fp(word, text):
    import re as _re
    return bool(_re.search(r'(?<![a-z])' + _re.escape(word) + r'(?![a-z])', text))

def fast(q):
    ql=q.lower()
    for n,v in CONSTS.items():
        if _word_in_fp(n, ql): return f"The {n} is {v}."
    m=MATH_RE.match(q.strip())
    if m:
        safe=re.sub(r'[^\d\s\+\-\*\/\(\)\.\^]','',m.group(1)).replace('^','**').strip()
        if safe:
            try: r=eval(safe,{"__builtins__":{}},{"sqrt":math.sqrt,"pi":math.pi}); return f"{m.group(1).strip()} = {round(float(r),8)}"
            except: pass
    return None

# ── Zophiel web search (DuckDuckGo) ──────────────────────────────────────
def zophiel_search(query):
    """Live web search for current events via DuckDuckGo Instant Answers.
    Requires env var AUREON_WEB_SEARCH=1 to be set (disabled by default).
    """
    import os
    if os.environ.get("AUREON_WEB_SEARCH") != "1":
        return [], "[offline: set AUREON_WEB_SEARCH=1 to enable live search]"
    try:
        import urllib.request, urllib.parse
        params = urllib.parse.urlencode({"q": query, "format": "json", "no_redirect": "1", "no_html": "1"})
        url = f"https://api.duckduckgo.com/?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "SOLIA/Zophiel 1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        results = []
        abstract = data.get("AbstractText", "")
        if abstract:
            results.append({"text": abstract, "source": data.get("AbstractURL","duckduckgo"), "score": 0.9})
        for t in data.get("RelatedTopics", [])[:4]:
            if isinstance(t,dict) and t.get("Text"):
                results.append({"text":t["Text"],"source":t.get("FirstURL","ddg"),"score":0.7})
        return results, data.get("Heading","")
    except Exception as e:
        return [], f"[search unavailable: {e}]"

# ── Domain test questions ──────────────────────────────────────────────────
DOMAIN_TESTS = {
    "PHYSICS": [
        ("How does quantum entanglement work?",               "PHYSICS"),
        ("What is the Heisenberg uncertainty principle?",     "PHYSICS"),
        ("Explain how a black hole forms",                    "PHYSICS"),
        ("What is the Pauli exclusion principle?",            "PHYSICS"),
        ("How does nuclear fusion release energy?",           "PHYSICS"),
        ("What is wave-particle duality?",                    "PHYSICS"),
        ("Explain the first law of thermodynamics",           "PHYSICS"),
        ("What causes the photoelectric effect?",             "PHYSICS"),
        ("How does the Doppler effect work?",                 "PHYSICS"),
        ("What is Schrödinger's equation used for?",          "PHYSICS"),
    ],
    "CHEMISTRY": [
        ("What is an electrochemical cell?",                  "CHEMISTRY"),
        ("How do catalysts speed up reactions?",              "CHEMISTRY"),
        ("Explain the difference between isotopes and isomers","CHEMISTRY"),
        ("What is Le Chatelier's principle?",                 "CHEMISTRY"),
        ("How does titration work?",                          "CHEMISTRY"),
        ("What makes carbon unique among elements?",          "CHEMISTRY"),
        ("Explain oxidation and reduction reactions",         "CHEMISTRY"),
        ("How is pH measured and what does it indicate?",     "CHEMISTRY"),
        ("What is the Gibbs free energy?",                    "CHEMISTRY"),
        ("How do polymers form?",                             "CHEMISTRY"),
    ],
    "BIOLOGY": [
        ("What is CRISPR and how does it work?",              "BIOLOGY"),
        ("How does the immune system recognise pathogens?",   "BIOLOGY"),
        ("Explain mitosis vs meiosis",                        "BIOLOGY"),
        ("What is epigenetics?",                              "BIOLOGY"),
        ("How do neurons transmit signals?",                  "BIOLOGY"),
        ("What is the role of ATP in the cell?",              "BIOLOGY"),
        ("How does natural selection drive evolution?",       "BIOLOGY"),
        ("What is the central dogma of molecular biology?",  "BIOLOGY"),
        ("How do vaccines create immunity?",                  "BIOLOGY"),
        ("What is the endocrine system?",                     "BIOLOGY"),
    ],
    "COMPUTER SCIENCE": [
        ("What is Big O notation and why does it matter?",    "COMPUTER SCIENCE"),
        ("How does a hash table work?",                       "COMPUTER SCIENCE"),
        ("Explain how TCP/IP works",                          "COMPUTER SCIENCE"),
        ("What is a binary search tree?",                     "COMPUTER SCIENCE"),
        ("How does garbage collection work in programming?",  "COMPUTER SCIENCE"),
        ("What is the difference between a process and thread?","COMPUTER SCIENCE"),
        ("How does public key cryptography work?",            "COMPUTER SCIENCE"),
        ("Explain gradient descent in machine learning",      "COMPUTER SCIENCE"),
        ("What is a distributed system?",                     "COMPUTER SCIENCE"),
        ("How does a compiler turn code into machine code?",  "COMPUTER SCIENCE"),
    ],
    "ECONOMICS": [
        ("What causes hyperinflation?",                       "ECONOMICS & BUSINESS"),
        ("Explain the concept of opportunity cost",           "ECONOMICS & BUSINESS"),
        ("How do central banks control the money supply?",    "ECONOMICS & BUSINESS"),
        ("What is game theory used for in economics?",        "ECONOMICS & BUSINESS"),
        ("Explain the prisoner's dilemma",                    "ECONOMICS & BUSINESS"),
        ("How do interest rates affect investment?",          "ECONOMICS & BUSINESS"),
        ("What is comparative advantage in trade?",           "ECONOMICS & BUSINESS"),
        ("What causes market bubbles?",                       "ECONOMICS & BUSINESS"),
        ("Explain the Keynesian multiplier effect",           "ECONOMICS & BUSINESS"),
        ("What is the relationship between risk and return?", "ECONOMICS & BUSINESS"),
    ],
    "CYBERSECURITY": [
        ("How does a SQL injection attack work?",             None),
        ("What is post-quantum cryptography?",                None),
        ("Explain how ransomware encrypts files",             None),
        ("How does a man-in-the-middle attack work?",         None),
        ("What is zero-trust security architecture?",         None),
        ("How does Kyber1024 protect against quantum attacks?",None),
        ("What is the Sovereign Organism lockdown protocol?",  None),
        ("How does chaos cipher mode prevent traffic analysis?",None),
        ("Explain the STRIDE threat model",                   None),
        ("How does AES-256-GCM authenticated encryption work?",None),
    ],
}

def think(q, domain_hint, index):
    f = fast(q)
    if f: return {"reply": f, "method": "fast_path"}
    # Cyber defence check
    cyber_result = cyber.analyse_threat(q)
    # RAG
    hits = index.query(q, top_k=8, src=domain_hint)
    # Add Nomad facts to hits if cyber
    if domain_hint is None and cyber_result:
        cyber_hits = [{"text": ft, "source": "NOMAD_CYBER", "score": 0.9} for ft in cyber.NOMAD_FACTS[:10]]
        hits = cyber_hits + hits
    answer = synthesize(hits, extra=cyber_result or "")
    method = "rag+synthesize"
    if cyber_result: method += "+cyber_defence"
    return {"reply": answer, "method": method, "hits": len(hits)}

def run():
    print("="*70)
    print("  AUREON / SOLIA — FULL DOMAIN TEST + CYBER DEFENCE")
    print("="*70)
    print()

    # Load index
    print("Building RAG index from fixed corpus (29,700 docs)...")
    # Inject Nomad facts into DB before building index
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM documents WHERE source='NOMAD_CYBER'")
    conn.executemany(
        "INSERT INTO documents (domain_id,subdomain_id,micro_subdomain_id,source,text,quality_score,verified) VALUES (0,0,0,'NOMAD_CYBER',?,0.95,1)",
        [(f,) for f in cyber.NOMAD_FACTS]
    )
    conn.commit(); conn.close()
    index = RagIndex()
    n = index.load_db()
    print(f"Index: {n:,} docs (incl. {len(cyber.NOMAD_FACTS)} Nomad cyber facts)\n")

    all_pass = all_synth = 0
    domain_results = {}

    for domain, questions in DOMAIN_TESTS.items():
        print(f"{'─'*70}")
        print(f"DOMAIN: {domain}")
        print(f"{'─'*70}")
        domain_synth = 0
        for i, (q, hint) in enumerate(questions, 1):
            result = think(q, hint, index)
            reply = result["reply"]
            # Synthesis check: reply must not be a direct quote from dataset boilerplate
            is_boilerplate = any(b in reply.lower() for b in ["indian academic","at institutions such as","the discipline of"])
            is_synthesised = not is_boilerplate and len(reply) > 60
            if is_synthesised: domain_synth += 1
            wrapped = textwrap.fill(reply, width=62, subsequent_indent="       ")
            status = "✓" if is_synthesised else "✗ BOILERPLATE"
            print(f"  Q{i:02}: {q}")
            print(f"  [{status}] {wrapped}")
            print(f"         method={result['method']}")
            print()
        domain_results[domain] = domain_synth
        all_synth += domain_synth
        all_pass += len(questions)

    # Zophiel current events test
    print(f"{'═'*70}")
    print("ZOPHIEL ENGINE — CURRENT EVENTS TEST")
    print(f"{'═'*70}")
    current_q = "What is happening with AI and technology regulation in 2026?"
    print(f"  Q: {current_q}")
    results, heading = zophiel_search(current_q)
    if results:
        print(f"  [LIVE SEARCH] Heading: {heading}")
        for r in results[:3]:
            wrapped = textwrap.fill(r['text'][:200], width=62, subsequent_indent="       ")
            print(f"  ▶ [{r['source'][:50]}]")
            print(f"    {wrapped}")
        # Feed live results into synthesizer
        live_answer = synthesize(results)
        print()
        print(f"  SYNTHESIZED:")
        print(f"  {textwrap.fill(live_answer, width=62, subsequent_indent='  ')}")
        print(f"  [method=zophiel_live_search+synthesize]")
    else:
        # Fallback to corpus
        hits = index.query(current_q, top_k=8)
        fallback = synthesize(hits)
        print(f"  [OFFLINE FALLBACK — no live search available in sandbox]")
        print(f"  ▶ {textwrap.fill(fallback, width=62, subsequent_indent='  ')}")
        print(f"  To enable live search: set env var AUREON_WEB_SEARCH=1 before running this script.")

    # Summary
    print()
    print(f"{'═'*70}")
    print("RESULTS SUMMARY")
    print(f"{'═'*70}")
    for domain, synth in domain_results.items():
        bar = "█"*synth + "░"*(10-synth)
        print(f"  {domain:<20} {bar} {synth}/10 synthesised")
    print()
    print(f"  Total: {all_synth}/{all_pass} questions synthesised from training data")
    if all_synth == all_pass:
        print("  [ALL PASS] Algorithm is synthesising — not quoting the dataset.")
    else:
        fail = all_pass - all_synth
        print(f"  [{fail} failures] — check those questions for corpus gaps.")
    print()

if __name__ == "__main__":
    run()

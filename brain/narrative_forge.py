"""
narrative_forge.py — ZOPHIEL NARRATIVE FORGE BRAIN
==================================================
Code-as-narrative comprehension, logic/security audit, and rebuild module.

Core law: code is a STORY. Every function is a character, every data flow a plot
line, every condition a choice, every exception the story breaking, every security
flaw a door the author forgot to lock.

Zophiel reads code, retells it as a plain-language story, audits the story through
three lenses (logic, narrative, security), rebuilds a corrected story explaining
what was broken and how it is fixed, then STOPS at a hard approval gate. Code is
only forged from an explicitly approved narrative.

Six-phase pipeline, in strict order — never skip, never reorder:
  1 TRANSLATE   code -> human narrative
  2 COMPREHEND  lock in purpose / assumptions / trust boundaries
  3 AUDIT       find logic flaws, broken narratives, security holes
  4 REBUILD     corrected narrative + what-was-broken / how-fixed
  5 APPROVAL    HARD STOP — wait for the user
  6 FORGE       approved narrative -> code (only after explicit approval)

This module is deterministic for phases 1-4 (static analysis). Phase 6 (forging
new code) genuinely requires generation and is delegated to the optional writer
(brain.mind.rag_writer); without it, the approved fixes are still described.

963Hz // Aureon Truth Engine
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

NARRATIVE_FORGE_DOCTRINE = (
    "Code is a story. If you can't retell it, you don't understand it. "
    "Comprehension before critique. Every external input is a hostile stranger "
    "until validated. A broken narrative is any thread that contradicts, dangles, "
    "or leaks. A security flaw is a door the author forgot to lock. Fix the "
    "disease, not the symptom. The approval gate is sacred — never forge code "
    "without explicit approval."
)

_AXIOMS = (
    "Code is a story. If you can't retell it, you don't understand it.",
    "Comprehension before critique.",
    "Every external input is a hostile stranger until validated.",
    "A broken narrative is any thread that contradicts, dangles, or leaks.",
    "A security flaw is a door the author forgot to lock.",
    "Fix the disease, not the symptom.",
    "Preserve purpose — repair the story, never replace its meaning.",
    "The approval gate is sacred. Never forge code without explicit approval.",
    "Forged code must map back, line by line, to the approved narrative.",
    "If the approved story is wrong, stop and surface it — never deviate silently.",
)

Severity = str  # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"


@dataclass(frozen=True)
class Finding:
    lens: str          # LOGIC | NARRATIVE | SECURITY
    name: str
    line: int
    severity: Severity
    why: str           # why it breaks the story
    fix: str           # before -> after, in human language

    def report_line(self) -> str:
        return f"[{self.lens}] {self.name} — line {self.line} — {self.why} — {self.severity}"


# ─── Phase detection ──────────────────────────────────────────────────────────

_FENCE_RE = re.compile(r"```[a-zA-Z0-9_+-]*\n(.*?)```", re.DOTALL)
_FORGE_INTENT_RE = re.compile(
    r"\b(review|audit|analyse|analyze|check|critique|forge|rebuild|refactor|"
    r"find (the )?(bug|bugs|flaw|flaws|vulnerab|security|issue|issues)|"
    r"what.?s wrong with|is this code|secure\b|broken narrative|narrative forge)\b",
    re.I,
)
_CODE_SHAPE_RE = re.compile(
    r"(def |class |function |=>|import |#include|public |private |"
    r"const |let |var |SELECT |INSERT |if\s*\(|;\s*$)", re.M)
_APPROVE_RE = re.compile(
    r"^\s*(approve|approved|go ahead|build it|forge it|yes do it|do it|ship it|"
    r"yes,? forge|make it)\b", re.I)


def extract_code(text: str) -> tuple[str, str]:
    """Pull a code block from the message. Returns (code, language_hint)."""
    m = _FENCE_RE.search(text)
    if m:
        lang_m = re.match(r"```([a-zA-Z0-9_+-]+)", text[m.start():])
        return m.group(1).strip(), (lang_m.group(1).lower() if lang_m else "")
    return "", ""


def looks_like_code(text: str) -> bool:
    return bool(_CODE_SHAPE_RE.search(text)) and text.count("\n") >= 2


def is_forge_request(text: str) -> bool:
    """True when the user is submitting code for review/audit/rebuild."""
    if not text:
        return False
    code, _ = extract_code(text)
    if code:
        return True
    # No fence: require both code-shaped content AND review intent.
    return looks_like_code(text) and bool(_FORGE_INTENT_RE.search(text))


def is_approval(text: str) -> bool:
    return bool(_APPROVE_RE.match(text or ""))


# ─── Phase 1: TRANSLATE — code into a plain story ─────────────────────────────

def _guess_language(code: str, hint: str) -> str:
    if hint:
        return hint
    if re.search(r"\bdef \w+\(|\bimport \w+|print\(", code):
        return "python"
    if re.search(r"\bfunction\b|=>|const |let |console\.log", code):
        return "javascript"
    if re.search(r"\b#include\b|std::|int main", code):
        return "c/c++"
    if re.search(r"\bSELECT\b|\bINSERT\b|\bUPDATE\b", code, re.I):
        return "sql"
    return "unknown"


def translate(code: str, language: str = "") -> str:
    lang = _guess_language(code, language)
    funcs = re.findall(r"(?:def|function)\s+(\w+)", code)
    classes = re.findall(r"class\s+(\w+)", code)
    imports = re.findall(r"(?:^|\n)\s*(?:import|from|#include|require)\b[^\n]*", code)
    returns = re.findall(r"\breturn\b[^\n]*", code)

    lines = ["THE STORY (as written):"]
    lines.append(f"1. The story is written in {lang} and runs about "
                 f"{code.count(chr(10)) + 1} lines.")
    if imports:
        lines.append(f"2. It opens by borrowing {len(imports)} tool(s) from "
                     f"elsewhere (imports).")
    if classes:
        lines.append(f"3. It introduces {len(classes)} structure(s): "
                     f"{', '.join(classes[:6])}.")
    if funcs:
        lines.append(f"4. The characters (functions) are: {', '.join(funcs[:8])}"
                     + (" ..." if len(funcs) > 8 else "") + ".")
    else:
        lines.append("4. There are no named characters — it is a straight-line script.")
    choices = len(re.findall(r"\bif\b", code))
    loops = len(re.findall(r"\b(for|while)\b", code))
    if choices:
        lines.append(f"5. The plot makes {choices} choice(s) (if-branches) and "
                     f"repeats {loops} chapter(s) (loops).")
    if returns:
        lines.append(f"6. The story is meant to end by handing back a result "
                     f"({len(returns)} return point(s)).")
    return "\n".join(lines)


# ─── Phase 2: COMPREHEND — purpose, assumptions, trust boundaries ─────────────

_TRUST_SOURCES = (
    ("request.", "an incoming web request"),
    ("input(", "interactive user input"),
    ("sys.argv", "command-line arguments"),
    ("os.environ", "the environment / config"),
    ("open(", "a file on disk"),
    (".read(", "an external stream"),
    ("recv(", "the network"),
    ("json.loads", "parsed external data"),
    ("getenv", "the environment / config"),
)


def comprehend(code: str, language: str = "") -> dict:
    docstring = ""
    dm = re.search(r'"""(.*?)"""', code, re.DOTALL)
    if dm:
        docstring = dm.group(1).strip().split("\n")[0].strip()
    funcs = re.findall(r"(?:def|function)\s+(\w+)", code)
    purpose = docstring or (
        f"do the work of {funcs[0]!r}" if funcs else "run a short script")

    assumptions: list[str] = []
    if "if " not in code and "try" not in code:
        assumptions.append("It assumes nothing ever goes wrong — no error handling.")
    if re.search(r"\[\s*0\s*\]|\[0\]", code):
        assumptions.append("It assumes a list/string is never empty (indexes [0]).")
    if re.search(r"int\(|float\(", code):
        assumptions.append("It assumes inputs are always valid numbers.")
    if "request." in code and "auth" not in code.lower():
        assumptions.append("It appears to trust the caller without checking who they are.")

    boundaries = [desc for token, desc in _TRUST_SOURCES if token in code]
    return {
        "purpose": purpose,
        "assumptions": assumptions or ["No obvious unstated assumptions detected."],
        "trust_boundaries": boundaries or ["No external/untrusted data crosses in."],
    }


# ─── Phase 3: AUDIT — three lenses ────────────────────────────────────────────

# Each rule: (lens, name, severity, line-regex, why, human fix)
_RULES: list[tuple[str, str, str, re.Pattern, str, str]] = [
    # SECURITY — unlocked doors
    ("SECURITY", "Code injection via eval/exec", "CRITICAL",
     re.compile(r"\b(eval|exec)\s*\("),
     "untrusted text can be executed as code (a stranger writing their own commands into your story)",
     "Before: any string could become a command. After: parse the value explicitly or use a safe lookup; never eval external input."),
    ("SECURITY", "Hardcoded secret", "HIGH",
     re.compile(r"(?i)(password|passwd|secret|api[_-]?key|token|private[_-]?key)\s*=\s*['\"][^'\"]{4,}['\"]"),
     "a key/password is written into the story in plain sight; anyone reading the code owns it",
     "Before: the secret lived in the source. After: read it from an environment variable / secret manager."),
    ("SECURITY", "SQL built by string-joining", "CRITICAL",
     re.compile(r"""(?ix)
        (['"][^'"]*\b(select|insert|update|delete|drop)\b[^'"]*['"]+\s*[+%])  # "SELECT..." +
        | ([+%]\s*\w+\s*[+%]?\s*['"][^'"]*\b(where|values|set|from)\b)         # + user + "WHERE
        | (f['"][^'"]*\b(select|insert|update|delete)\b[^'"]*\{)               # f"SELECT...{x}
     """),
     "user data is glued into a SQL command, letting a stranger rewrite the query (SQL injection)",
     "Before: the query was assembled from raw input. After: use parameterized queries (placeholders), never string concatenation."),
    ("SECURITY", "shell=True with a command string", "HIGH",
     re.compile(r"shell\s*=\s*True"),
     "an external value can spill into the shell and run extra commands (command injection)",
     "Before: the shell parsed the whole string. After: pass an argument list and shell=False."),
    ("SECURITY", "Non-constant-time secret comparison", "MEDIUM",
     re.compile(r"(?i)(\b(pw|pass|password|token|secret|signature|mac|hmac|digest|api[_-]?key)\w*\s*==)"
                r"|(==\s*\b(pw|pass|password|token|secret|signature|mac|hmac|digest|api[_-]?key)\w*)"),
     "comparing secrets with == leaks timing, letting an attacker guess them byte by byte",
     "Before: == revealed how much matched. After: use a constant-time compare (hmac.compare_digest)."),
    ("SECURITY", "Predictable randomness for a secret", "HIGH",
     re.compile(r"random\.(random|randint|choice|randrange)\s*\([^)]*\)"),
     "ordinary randomness is predictable; if it guards a token/password an attacker can reproduce it",
     "Before: predictable random. After: use the secrets module for anything security-sensitive."),
    ("SECURITY", "Weak hash for passwords", "MEDIUM",
     re.compile(r"\b(md5|sha1)\s*\("),
     "MD5/SHA1 are fast and broken for passwords; they can be brute-forced",
     "Before: a weak/fast hash. After: use a slow password hash (bcrypt/argon2/PBKDF2) with a salt."),
    ("SECURITY", "TLS verification disabled", "HIGH",
     re.compile(r"verify\s*=\s*False|InsecureRequestWarning|CERT_NONE"),
     "turning off certificate checks lets an attacker impersonate the server (man-in-the-middle)",
     "Before: the door trusted any certificate. After: keep verification on; pin or fix the cert chain."),
    ("SECURITY", "Untrusted deserialization", "HIGH",
     re.compile(r"(pickle|yaml)\.(load|loads)\s*\("),
     "loading pickled/unsafe-YAML data from outside can execute arbitrary code",
     "Before: external bytes were trusted. After: use JSON, or yaml.safe_load, for untrusted input."),
    # NARRATIVE — dangling / broken threads
    ("NARRATIVE", "Swallowed error (bare except: pass)", "MEDIUM",
     re.compile(r"except[^\n:]*:\s*(\n\s*pass|\s*pass)\b"),
     "the story breaks and nobody is told — a failure vanishes silently",
     "Before: the error disappeared. After: log it (or handle it) so the blind spot is visible."),
    ("NARRATIVE", "Bare except catches everything", "LOW",
     re.compile(r"\bexcept\s*:\s*"),
     "catching everything hides real bugs and even Ctrl-C; the thread is too greedy",
     "Before: except: caught all. After: catch the specific exception type you expect."),
    ("NARRATIVE", "Resource opened without 'with'", "LOW",
     re.compile(r"=\s*open\s*\([^)]*\)"),
     "a file/handle may be left open if the story breaks before it is closed (a thread never tied off)",
     "Before: a dangling handle. After: use 'with open(...) as f:' so it always closes."),
    ("NARRATIVE", "Unfinished thread (TODO/FIXME)", "LOW",
     re.compile(r"#\s*(TODO|FIXME|XXX|HACK)\b"),
     "the author marked an unfinished thread that may still be dangling",
     "Before: a known gap left open. After: resolve it, or track it deliberately."),
    # LOGIC — the story doesn't add up
    ("LOGIC", "Dead ternary (both arms identical)", "MEDIUM",
     re.compile(r"(['\"][^'\"]+['\"])\s+if\s+.+?\s+else\s+\1"),
     "a choice is computed then thrown away — both outcomes are the same (a light switch labelled 'on' on both sides)",
     "Before: the condition did nothing. After: make the two arms actually differ, or drop the dead guard."),
    ("LOGIC", "Comparison to None with == / !=", "LOW",
     re.compile(r"[!=]=\s*None\b"),
     "identity should use 'is' / 'is not'; == can be fooled by custom equality",
     "Before: == None. After: 'is None' / 'is not None'."),
    ("LOGIC", "Always-true loop guard with no break", "LOW",
     re.compile(r"while\s+True\s*:(?![\s\S]*\bbreak\b)"),
     "a chapter that repeats forever with no exit — the story can never end",
     "Before: an endless loop. After: add a real exit condition or a break."),
    ("LOGIC", "Mutable default argument", "MEDIUM",
     re.compile(r"def\s+\w+\([^)]*=\s*(\[\]|\{\})[^)]*\)"),
     "a shared list/dict default remembers across calls — state leaks between unrelated stories",
     "Before: def f(x=[]). After: def f(x=None): then x = x or [] inside."),
]


def audit(code: str, language: str = "") -> list[Finding]:
    """Scan the whole code (so multi-line patterns like 'except: pass' are caught)
    and report the line of the FIRST match for each rule. One finding per rule."""
    findings: list[Finding] = []
    for lens, name, sev, rx, why, fix in _RULES:
        m = rx.search(code)
        if not m:
            continue
        line_no = code.count("\n", 0, m.start()) + 1
        findings.append(Finding(lens, name, line_no, sev, why, fix))
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    findings.sort(key=lambda f: (order.get(f.severity, 9), f.line))
    return findings


# ─── Phase 4: REBUILD — recommendation narrative ──────────────────────────────

def rebuild(findings: list[Finding], comprehension: dict) -> str:
    out = ["THE REBUILT STORY (recommendation):"]
    out.append(f"Purpose stays the same — {comprehension['purpose']} — only made "
               f"true to itself and safe.\n")
    if not findings:
        out.append("No broken threads or unlocked doors were found by the three "
                   "lenses. The story holds together as written.")
        return "\n".join(out)
    out.append("WHAT WAS BROKEN AND HOW TO FIX IT:")
    for f in findings:
        out.append(f"  • [{f.severity}] {f.name} (line {f.line})")
        out.append(f"      {f.fix}")
    return "\n".join(out)


# ─── Orchestrator with the hard approval gate ─────────────────────────────────

# Pending approved-pending narratives, keyed by session. In-memory by design:
# the approval gate must not survive a restart as a silent yes.
_PENDING: dict[str, dict] = {}


def _format_report(code: str, language: str) -> tuple[str, list[Finding], dict]:
    story = translate(code, language)
    comp = comprehend(code, language)
    findings = audit(code, language)
    parts = [story, ""]
    parts.append("PURPOSE: " + comp["purpose"])
    parts.append("ASSUMPTIONS:")
    parts += [f"  - {a}" for a in comp["assumptions"]]
    parts.append("TRUST BOUNDARIES (where outside data crosses in):")
    parts += [f"  - {b}" for b in comp["trust_boundaries"]]
    parts.append("")
    parts.append("BROKEN NARRATIVE REPORT:")
    if findings:
        parts += [f"  {f.report_line()}" for f in findings]
    else:
        parts.append("  No logic, narrative, or security breaks detected by the three lenses.")
    parts.append("")
    parts.append(rebuild(findings, comp))
    parts.append("")
    parts.append("APPROVAL REQUIRED:")
    parts.append('  "Do you approve this rebuilt narrative? Reply APPROVE to forge '
                 'the corrected code, or tell me what to adjust."')
    return "\n".join(parts), findings, comp


def process(text: str, session_id: str | None = None,
            forge_fn: Callable[[str, str], str] | None = None) -> dict | None:
    """Run the Narrative Forge pipeline.

    Returns a payload dict with the report + approval gate (phases 1-5), or the
    forged result on approval (phase 6), or None if this is not a forge request.
    """
    sid = session_id or "_default"

    # Phase 6 trigger: explicit approval of a pending narrative.
    if is_approval(text) and sid in _PENDING:
        pending = _PENDING.pop(sid)
        forged = _forge(pending, forge_fn)
        return {"reply": forged, "method": "narrative_forge(forge)",
                "phase": "forge", "is_forge": True}

    if not is_forge_request(text):
        return None

    code, hint = extract_code(text)
    if not code:
        code = text  # whole message is code-shaped
    language = _guess_language(code, hint)

    report, findings, comp = _format_report(code, language)
    _PENDING[sid] = {"code": code, "language": language,
                     "findings": findings, "comprehension": comp}
    return {"reply": report, "method": "narrative_forge(audit)",
            "phase": "approval_gate", "is_forge": True,
            "findings": len(findings)}


def _forge(pending: dict, forge_fn: Callable[[str, str], str] | None) -> str:
    """Phase 6 — produce the corrected code from the approved narrative.

    Real code generation requires the writer model. When it is configured we hand
    it the original code plus the fix narrative; otherwise we hand back the
    concrete, ordered fix checklist so the work is still actionable.
    """
    findings: list[Finding] = pending["findings"]
    if not findings:
        return ("Approved. There were no breaks to repair — the original story "
                "already holds. Nothing to forge.")
    if forge_fn is not None:
        narrative = "\n".join(
            f"- Fix [{f.severity}] {f.name} (line {f.line}): {f.fix}" for f in findings)
        try:
            generated = forge_fn(pending["code"], narrative)
            if generated and generated.strip():
                return ("FORGED CODE (from the approved narrative):\n\n" + generated
                        + "\n\nEach change maps back to a fix in the approved report.")
        except Exception:
            pass
    # No writer model: deliver the precise, ordered repair plan instead of guessing.
    lines = ["Approved. Forging requires the writer model (set ZOPHIEL_LLM_API_KEY) "
             "to rewrite the code. Here is the exact, ordered repair plan to apply:\n"]
    for i, f in enumerate(findings, 1):
        lines.append(f"{i}. [{f.severity}] {f.name} (line {f.line})")
        lines.append(f"   {f.fix}")
    return "\n".join(lines)

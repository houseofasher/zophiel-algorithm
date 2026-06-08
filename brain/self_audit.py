"""Self-audit — read-only codebase analysis for security and quality."""

from __future__ import annotations

import ast
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent


def _scan_file(path: Path) -> dict[str, Any]:
    issues: list[str] = []
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = getattr(node.func, "id", None) or getattr(
                    getattr(node.func, "attr", None), "__class__", ""
                )
                if func == "eval":
                    issues.append(f"line {node.lineno}: unsafe eval()")
                if func == "exec":
                    issues.append(f"line {node.lineno}: unsafe exec()")
    except SyntaxError as exc:
        issues.append(f"syntax error: {exc}")
    except Exception as exc:
        issues.append(f"scan error: {exc}")
    return {"path": str(path.relative_to(_ROOT)), "issues": issues}


def run_self_audit(max_files: int = 120) -> dict[str, Any]:
    py_files = sorted(_ROOT.rglob("*.py"))[:max_files]
    results = []
    for f in py_files:
        if ".git" in f.parts or "__pycache__" in f.parts:
            continue
        results.append(_scan_file(f))
    flagged = [r for r in results if r["issues"]]
    return {
        "files_scanned": len(results),
        "files_with_issues": len(flagged),
        "flagged": flagged,
        "clean": len(results) - len(flagged),
    }


def format_self_audit_report(audit: dict[str, Any]) -> str:
    lines = [
        f"Files scanned: {audit['files_scanned']}",
        f"Clean: {audit['clean']}",
        f"With issues: {audit['files_with_issues']}",
    ]
    for item in audit.get("flagged", []):
        lines.append(f"  {item['path']}: {'; '.join(item['issues'])}")
    return "\n".join(lines)


def is_self_audit_request(text: str) -> bool:
    """Return True if the user message is asking Aureon to audit itself."""
    t = text.lower().strip()
    signals = [
        "self audit", "self-audit", "audit yourself", "audit your code",
        "check your code", "scan yourself", "code audit", "code review aureon",
        "what bugs", "what errors in your", "how healthy is your",
    ]
    return any(s in t for s in signals)

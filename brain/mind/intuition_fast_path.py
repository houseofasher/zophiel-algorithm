"""
Intuition Fast-Path — Quick pattern-matched answers for common question types.
Bypasses full RAG + logic pipeline when the answer can be determined instantly
from structural question patterns (maths, conversions, definitions of constants, etc.).
Returns None when it cannot answer fast — signals the orchestrator to use full pipeline.
"""
from __future__ import annotations
import re, math
from dataclasses import dataclass

@dataclass
class FastAnswer:
    answer: str
    confidence: float
    method: str   # e.g. 'math', 'constant', 'definition', 'conversion'

_CONSTANTS: dict[str, tuple[str, str]] = {
    'speed of light':          ('299,792,458 m/s', 'physics constant'),
    'planck':                  ("6.626 × 10⁻³⁴ J·s", 'physics constant'),
    'boltzmann':               ("1.381 × 10⁻²³ J/K", 'physics constant'),
    'avogadro':                ("6.022 × 10²³ mol⁻¹", 'chemistry constant'),
    'gravitational constant':  ("6.674 × 10⁻¹¹ N·m²/kg²", 'physics constant'),
    'pi':                      ('3.14159265358979...', 'mathematical constant'),
    'euler':                   ("e ≈ 2.71828182845...", 'mathematical constant'),
    'golden ratio':            ('φ ≈ 1.61803398874...', 'mathematical constant'),
}

_UNIT_CONV: list[tuple[re.Pattern, callable]] = [
    (re.compile(r'(\d+\.?\d*)\s*km\s+(?:to|in)\s+miles?', re.I),
     lambda m: f"{float(m.group(1))} km = {float(m.group(1)) * 0.621371:.4f} miles"),
    (re.compile(r'(\d+\.?\d*)\s*miles?\s+(?:to|in)\s+km', re.I),
     lambda m: f"{float(m.group(1))} miles = {float(m.group(1)) * 1.60934:.4f} km"),
    (re.compile(r'(\d+\.?\d*)\s*(?:°?C|celsius)\s+(?:to|in)\s+(?:°?F|fahrenheit)', re.I),
     lambda m: f"{float(m.group(1))}°C = {float(m.group(1)) * 9/5 + 32:.2f}°F"),
    (re.compile(r'(\d+\.?\d*)\s*(?:°?F|fahrenheit)\s+(?:to|in)\s+(?:°?C|celsius)', re.I),
     lambda m: f"{float(m.group(1))}°F = {(float(m.group(1)) - 32) * 5/9:.2f}°C"),
    (re.compile(r'(\d+\.?\d*)\s*kg\s+(?:to|in)\s+(?:lbs?|pounds?)', re.I),
     lambda m: f"{float(m.group(1))} kg = {float(m.group(1)) * 2.20462:.4f} lbs"),
    (re.compile(r'(\d+\.?\d*)\s*(?:lbs?|pounds?)\s+(?:to|in)\s+kg', re.I),
     lambda m: f"{float(m.group(1))} lbs = {float(m.group(1)) * 0.453592:.4f} kg"),
]

_MATH_RE = re.compile(
    r'(?:what\s+is\s+|calculate\s+|compute\s+)?'
    r'([\d\s\+\-\*\/\(\)\^\.]+)'
    r'\s*(?:=\s*\?|equals?\??|result\??)?$',
    re.I,
)

def _try_math(expr: str) -> str | None:
    # sanitise: allow only digits, operators, parens, dots, spaces
    safe = re.sub(r'[^\d\s\+\-\*\/\(\)\.\^]', '', expr).strip()
    safe = safe.replace('^', '**')
    if not safe:
        return None
    try:
        result = eval(safe, {"__builtins__": {}}, {"sqrt": math.sqrt, "pi": math.pi})
        return str(round(float(result), 8))
    except Exception:
        return None

def fast_answer(query: str) -> FastAnswer | None:
    q = query.strip()

    # Constants
    q_low = q.lower()
    for name, (value, kind) in _CONSTANTS.items():
        if name in q_low:
            return FastAnswer(
                answer=f"The {name} is {value}.",
                confidence=0.99,
                method=f'constant:{kind}',
            )

    # Unit conversions
    for pat, fn in _UNIT_CONV:
        m = pat.search(q)
        if m:
            try:
                result = fn(m)
                return FastAnswer(answer=result, confidence=0.99, method='conversion')
            except Exception:
                pass

    # Simple arithmetic
    m = _MATH_RE.match(q)
    if m:
        result = _try_math(m.group(1))
        if result is not None:
            return FastAnswer(
                answer=f"{m.group(1).strip()} = {result}",
                confidence=0.99,
                method='math',
            )

    return None

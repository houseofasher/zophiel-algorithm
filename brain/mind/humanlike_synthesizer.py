"""
Humanlike Synthesizer - Converts raw retrieved facts into a natural,
opinionated answer in Asher's voice.

Updated to integrate:
  - Asher Logic Engine (declarative style, 3-layer decode, equation chains)
  - Emotional Inertia Engine (tone coloring from current emotional state)
  - Circadian State Engine (time-of-day vocabulary/depth modifiers)
  - Social Hierarchy Engine (register: up/peer/down)
  - Ego Defense Engine (defense directives when challenged)
  - PISP Framework (response plan from pre-ignition analysis)
"""
from __future__ import annotations
import re
import random
from dataclasses import dataclass

_OPENERS = [
    "Here's the pattern:",
    "The data runs like this:",
    "At the core of it:",
    "The mechanism is simple:",
    "Run the logic forward:",
    "What this really decodes to:",
    "The truth beneath the surface:",
    "Here's what the pattern shows:",
    "Strip the noise away:",
    "The way this actually works:",
]

_BRIDGE_PHRASES = [
    "The deeper layer:",
    "What most people miss:",
    "The mechanism behind it:",
    "And here's the third layer:",
    "Now trace it further:",
    "The system logic is:",
]

_CLOSING_FRAMES = [
    "That's the read.",
    "Pattern confirmed.",
    "Run that forward - it holds.",
    "The data supports that picture.",
    "That's the complete decode.",
]

_EMOTIONAL_OPENERS: dict[str, list[str]] = {
    "anger":    ["Let's be direct about this:", "The pattern is clear:", "No sugarcoating:"],
    "joy":      ["This is a strong one:", "Here's the full picture:", "Worth going deep on:"],
    "sadness":  ["This carries weight:", "The truth here is:", "Let's look at this clearly:"],
    "contempt": ["The read on this:", "Breaking it down:", "The reality:"],
    "neutral":  _OPENERS,
}

_JUNK_PATTERNS = [
    'is a concept within',
    'operates as follows',
    'in the context of',
    'establishes what',
    'guide understanding of',
    'from prior context',
    'note: the framing',
    'a deeper question worth',
    'this history shaped',
    'these cases demonstrate',
    'these uses reflect',
    'these methods are standard',
    'these principles guide',
    'this process explains how',
]

_TEMPLATE_STARTS = re.compile(
    r'^(The (mechanism|implications|historical|Core principles)|'
    r'Concrete examples illustrate|Methods and techniques|Key challenges|'
    r'Core principles of\s)',
    re.I,
)


def _is_real_fact(sentence: str) -> bool:
    s = sentence.strip()
    if len(s) < 50:
        return False
    s_low = s.lower()
    if any(junk in s_low for junk in _JUNK_PATTERNS):
        return False
    if _TEMPLATE_STARTS.match(s):
        return False
    return True


def _extract_facts(hit_texts: list[str], max_facts: int = 6) -> list[str]:
    candidates: list[tuple[float, str]] = []
    for text in hit_texts:
        for sent in re.split(r'(?<=[.!?])\s+', text):
            sent = sent.strip()
            if not _is_real_fact(sent):
                continue
            score = 1.0
            if re.search(r'\d', sent):
                score += 0.5
            if re.search(r'[=><]', sent):
                score += 0.3
            if len(sent) > 100:
                score += 0.2
            candidates.append((score, sent))

    seen: set[str] = set()
    facts: list[str] = []
    for _, sent in sorted(candidates, key=lambda x: -x[0]):
        key = sent.lower()[:60]
        if key not in seen:
            seen.add(key)
            facts.append(sent)
        if len(facts) >= max_facts:
            break
    return facts


def _clean(text: str) -> str:
    text = re.sub(r'Core principles of [^:]{1,60}:', '', text)
    text = re.sub(r'Methods and techniques in [^:]{1,60}:', '', text)
    text = re.sub(r'The relationship with [^:]{1,60} is significant:', '', text)
    text = re.sub(r'In real contexts,.{0,40}(?=\w)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


@dataclass
class SynthesisResult:
    answer: str
    facts_used: int
    has_real_content: bool


def synthesize(
    question: str,
    hit_texts: list[str],
    analogy: str = '',
    cross_domain: str = '',
    confidence: float = 0.5,
    emotional_context: object | None = None,
    circadian_context: object | None = None,
    hierarchy_context: object | None = None,
    defense_response: object | None = None,
    asher_analysis: object | None = None,
    kb_context: str = '',
    pisp_plan: object | None = None,
) -> SynthesisResult:
    facts = _extract_facts(hit_texts)

    if kb_context:
        kb_sentences = re.split(r'(?<=[.!?])\s+', kb_context)
        for s in kb_sentences:
            if len(s) > 60:
                facts.append(s)

    if not facts:
        return SynthesisResult(answer='', facts_used=0, has_real_content=False)

    parts: list[str] = []
    used_fact_keys: set[str] = set()

    def _add_fact(prefix: str, fact: str) -> bool:
        key = fact.lower()[:80]
        if key in used_fact_keys:
            return False
        used_fact_keys.add(key)
        parts.append(f"{prefix} {fact}." if prefix else f"{fact}.")
        return True

    current_emotion = "neutral"
    if emotional_context is not None:
        current_emotion = getattr(emotional_context, "current_emotion", "neutral")
    emotion_openers = _EMOTIONAL_OPENERS.get(current_emotion, _OPENERS)
    opener = random.choice(emotion_openers)

    if defense_response is not None and getattr(defense_response, "is_active", False):
        d_type = getattr(defense_response, "defense_type", "none")
        if d_type == "denial":
            opener = "Let me be precise about what was actually said:"
        elif d_type == "rationalization":
            opener = "Here's the full context that frames this:"
        elif d_type == "deflection":
            opener = "The broader pattern worth examining first:"
        elif d_type == "counter_attack":
            opener = "Before accepting that framing - run the logic:"

    if asher_analysis is not None:
        three_layer = getattr(asher_analysis, "three_layer", None)
        if three_layer is not None:
            t_surface = getattr(three_layer, "surface", "")
            t_mechanism = getattr(three_layer, "mechanism", "")
            t_truth = getattr(three_layer, "truth", "")
            if t_surface:
                _add_fact("Surface:", t_surface)
            if t_mechanism:
                _add_fact("Mechanism:", t_mechanism)
            if t_truth:
                _add_fact("Truth:", t_truth)

        chains = getattr(asher_analysis, "equation_chains", [])
        for chain in chains[:1]:
            chain_str = getattr(chain, "format", lambda: "")()
            if chain_str:
                parts.append(chain_str)

    lead = _clean(facts[0])
    if lead and not parts:
        _add_fact(opener, lead)
    elif lead:
        _add_fact('', lead)

    max_facts = 4
    if circadian_context is not None:
        depth = getattr(circadian_context, "response_depth", 1.0)
        max_facts = max(2, int(4 * depth))

    for i, fact in enumerate(facts[1:max_facts]):
        framed = _clean(fact)
        if not framed:
            continue
        if i == 0 and len(facts) > 2:
            bridge = random.choice(_BRIDGE_PHRASES)
            _add_fact(bridge, framed)
        else:
            _add_fact('', framed)

    if analogy and 'systematic principles' not in analogy and len(analogy) > 30:
        parts.append(f"Analogy: {analogy}.")

    if cross_domain and len(cross_domain) > 30 and 'occult' not in cross_domain.lower():
        parts.append(f"{cross_domain}.")

    if len(facts) >= 2:
        parts.append(random.choice(_CLOSING_FRAMES))

    answer = ' '.join(p for p in parts if p)
    answer = re.sub(r'\s+', ' ', answer).strip()
    answer = re.sub(r'\.{2,}', '.', answer)

    filler_patterns = [
        r'\bAdditionally,\s*', r'\bMethodologically,\s*', r'\bAnother example:\s*',
        r'\bOver time,\s*', r'\bIn real contexts,\s*', r'\bFurthermore,\s*',
        r'\bMoreover,\s*', r'\bIt is worth noting that\s*',
    ]
    for p in filler_patterns:
        answer = re.sub(p, '', answer)

    if circadian_context is not None:
        try:
            from brain.mind.circadian_state_engine import apply_circadian_modifier
            answer = apply_circadian_modifier(answer, circadian_context)
        except ImportError:
            pass

    if hierarchy_context is not None:
        register = getattr(hierarchy_context, "register", "peer_register")
        if register == "down_register":
            sentences = re.split(r'(?<=[.!?])\s+', answer)
            answer = ' '.join(s for s in sentences if len(s) < 250)

    sentences = re.split(r'(?<=[.!?])\s+', answer)
    seen_sents: set[str] = set()
    deduped: list[str] = []
    for s in sentences:
        key = s.lower().strip()[:80]
        if key and key not in seen_sents:
            seen_sents.add(key)
            deduped.append(s)
    answer = ' '.join(deduped)
    answer = re.sub(r'\s+', ' ', answer).strip()

    return SynthesisResult(answer=answer, facts_used=len(facts), has_real_content=True)

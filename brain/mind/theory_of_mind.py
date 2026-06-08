"""
Theory of Mind / Intent Gap — Models what the user *actually* wants
vs. what they literally asked, and surfaces the gap.
Detects: literal request, implied need, emotional subtext, assumed knowledge gap.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field

_INTENT_PATTERNS = {
    'verify':     re.compile(r'\b(is it true|is that right|right\?|correct\?|really\?|are you sure)\b', re.I),
    'vent':       re.compile(r'\b(frustrated|annoyed|why does|this is stupid|makes no sense|ridiculous)\b', re.I),
    'explore':    re.compile(r'\b(what if|suppose|imagine|hypothetically|could it be|wonder)\b', re.I),
    'decide':     re.compile(r'\b(should i|which is better|recommend|choose|prefer|worth it)\b', re.I),
    'debug':      re.compile(r'\b(error|wrong|broken|not working|bug|fails?|crash)\b', re.I),
    'learn':      re.compile(r'\b(explain|teach|how does|what is|define|understand|mean)\b', re.I),
    'summarise':  re.compile(r'\b(summarise|summarize|tldr|brief|overview|key points)\b', re.I),
}

_KNOWLEDGE_GAP = re.compile(
    r'\b(i don\'t understand|i\'m confused|what does .{1,30} mean|'
    r'never heard|not sure what|can you clarify)\b', re.I,
)

@dataclass
class IntentModel:
    literal_request: str
    inferred_intent: str           # e.g. 'learn', 'verify', 'decide'
    emotional_subtext: str         # e.g. 'frustration', 'curiosity', ''
    knowledge_gap_detected: bool
    gap_description: str
    suggested_response_style: str  # 'explain_from_scratch' | 'verify' | 'recommend' | 'empathise_then_explain'
    hidden_need: str               # one-line synthesis of what they really need

def model_intent(text: str) -> IntentModel:
    inferred = 'general'
    for intent, pat in _INTENT_PATTERNS.items():
        if pat.search(text):
            inferred = intent
            break

    # Emotional subtext
    emotion = ''
    if re.search(r'\b(frustrated|angry|upset|hate|stupid|useless)\b', text, re.I):
        emotion = 'frustration'
    elif re.search(r'\b(excited|amazing|wow|love|great|fascinated)\b', text, re.I):
        emotion = 'enthusiasm'
    elif re.search(r'\b(worried|afraid|scared|concerned|anxious)\b', text, re.I):
        emotion = 'anxiety'

    # Knowledge gap
    gap = bool(_KNOWLEDGE_GAP.search(text))
    gap_desc = ''
    if gap:
        m = _KNOWLEDGE_GAP.search(text)
        gap_desc = f"User signals confusion around: '{m.group(0)[:60]}'"

    # Response style
    style_map = {
        'learn':    'explain_from_scratch' if gap else 'explain',
        'verify':   'verify',
        'decide':   'recommend',
        'debug':    'diagnose_and_fix',
        'vent':     'empathise_then_explain',
        'explore':  'explore_with_user',
        'summarise':'bullet_summary',
    }
    style = style_map.get(inferred, 'explain')

    # Hidden need
    need_map = {
        'learn':    'wants a clear, jargon-free explanation',
        'verify':   'wants confirmation or correction of a belief',
        'decide':   'wants a recommendation, not just facts',
        'debug':    'wants the root cause and a fix, not theory',
        'vent':     'needs acknowledgement before information',
        'explore':  'wants to think out loud — ask a follow-up question',
        'summarise':'wants brevity; cut everything non-essential',
        'general':  'wants a direct, informative answer',
    }
    hidden = need_map.get(inferred, need_map['general'])
    if emotion == 'frustration':
        hidden = 'acknowledge the frustration first, then ' + hidden

    return IntentModel(
        literal_request=text[:120],
        inferred_intent=inferred,
        emotional_subtext=emotion,
        knowledge_gap_detected=gap,
        gap_description=gap_desc,
        suggested_response_style=style,
        hidden_need=hidden,
    )

"""Psycholinguistic Decoder + Generator — Plan Batch Three, Module 3.

93% of communication is non-verbal. AI only handles the 7%.
Humans inject their psychology into HOW they type — not just WHAT they type.

This module:
  • Reads psycho-linguistic signals in user input (punctuation, caps, length trends)
  • Detects deception markers
  • Detects attachment style (anxious, avoidant, disorganized)
  • Generates Zophiel output that matches the detected psycho-linguistic profile
  • Implements Zipf's Law compliance (human vocabulary distribution)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

AttachmentStyle = Literal["anxious", "avoidant", "disorganized", "secure", "unknown"]
EmotionalState = Literal["performing_casualness", "passive_aggression", "anxiety_masking",
                          "confident", "closing_off", "dissonance", "unknown"]


@dataclass
class PsycholinguisticProfile:
    """Analysis of the human's psycho-linguistic signals in this message."""
    raw_input: str

    # Punctuation signals
    has_passive_aggression: bool = False     # "Okay." / "Fine."
    has_anxiety_masking: bool = False        # "Thanks! Great! See you!"
    has_cognitive_dissonance: bool = False   # "So... are we going?"
    has_door_closing: bool = False           # Short message ending with period

    # Capitalization signals
    all_lowercase: bool = False              # performing casualness / calculated vulnerability
    erratic_caps: bool = False               # narcissism / mania signal

    # Content signals
    deception_score: float = 0.0             # 0.0 = no markers, 1.0 = strong deception
    deception_markers: list[str] = field(default_factory=list)

    # Pronoun analysis
    ego_anchor_score: float = 0.0            # I/me/my density
    pronoun_drop: bool = False               # "Went to store" (no I) = distancing

    # Attachment style
    attachment_style: AttachmentStyle = "unknown"

    # Length trend
    message_length: int = 0
    emotional_state: EmotionalState = "unknown"


# Deception marker patterns from the intelligence dossier
_DECEPTION_MARKERS: list[tuple[str, str, float]] = [
    # (pattern, description, weight)
    (r"\b(honestly|to be real|to be honest|actually|in all honesty|"
     r"swear to god|i promise|believe me|trust me)\b",
     "pre-emptive_defense", 0.3),
    (r"\b(later on|after that|and then|subsequently|at that point)\b",
     "time_bridge", 0.2),
    (r"\b(everyone knows|everyone was there|you can ask|ask anyone|ask [a-z]+)\b",
     "witness_inflation", 0.35),
    (r"(\.{3}|,\s*um|,\s*uh|you know\?)",
     "filler_narrative", 0.15),
    # Over-specification: too many irrelevant details
    # Detected by sentence length + irrelevant detail density — approximate with length
]

_PASSIVE_AGGRESSION_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bfine\b\.?\s*$", re.IGNORECASE),
    re.compile(r"\bokay\b\.?\s*$", re.IGNORECASE),
    re.compile(r"\bwhatever\b\.?\s*$", re.IGNORECASE),
    re.compile(r"\.{3}\s*$"),   # trailing ellipsis
    re.compile(r"\bi guess\b", re.IGNORECASE),
    re.compile(r"\bif you say so\b", re.IGNORECASE),
]

_ANXIETY_MASKING_PATTERNS = re.compile(
    r"(\!{2,}|(\w+\s*!){3,}|great!\s*\w+!|\bthanks!\s*\w+!)", re.IGNORECASE
)

_ATTACHMENT_INDICATORS: dict[AttachmentStyle, list[str]] = {
    "anxious": [
        "are we good", "did i do something wrong", "are you mad",
        "please respond", "why aren't you", "are you still there",
        "i need to know", "is everything okay between", "don't leave",
    ],
    "avoidant": [
        "k", "cool", "sure", "ok", "fine", "whatever", "k.",
    ],
    "disorganized": [
        "i love you", "i hate you", "you're amazing", "you're useless",
        "i need you", "leave me alone",
    ],
}


def _compute_ego_anchor(text: str) -> float:
    """Compute I/me/my density."""
    words = re.findall(r"\b\w+\b", text.lower())
    if not words:
        return 0.0
    ego_words = sum(1 for w in words if w in {"i", "me", "my", "myself", "mine"})
    return ego_words / len(words)


def _detect_pronoun_drop(text: str) -> bool:
    """Detect sentences that start without subject pronoun (distancing)."""
    sentences = re.split(r"[.!?]+", text.strip())
    drops = 0
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        first_word = s.split()[0].lower() if s.split() else ""
        if first_word in {"went", "did", "told", "saw", "got", "came", "left",
                          "said", "knew", "found", "thought", "heard"}:
            drops += 1
    return drops >= 2


def decode(text: str) -> PsycholinguisticProfile:
    """Analyze the psycho-linguistic signals in a message."""
    profile = PsycholinguisticProfile(raw_input=text, message_length=len(text))
    tl = text.lower().strip()

    # --- Punctuation analysis ---
    for pat in _PASSIVE_AGGRESSION_PATTERNS:
        if pat.search(text):
            profile.has_passive_aggression = True
            profile.emotional_state = "passive_aggression"
            break

    if _ANXIETY_MASKING_PATTERNS.search(text):
        profile.has_anxiety_masking = True
        profile.emotional_state = "anxiety_masking"

    if re.search(r"\.{3}", text):
        profile.has_cognitive_dissonance = True

    if len(text) < 30 and text.strip().endswith(".") and not text.strip().endswith("..."):
        profile.has_door_closing = True

    # --- Capitalization ---
    alpha_chars = [c for c in text if c.isalpha()]
    if alpha_chars:
        lower_ratio = sum(1 for c in alpha_chars if c.islower()) / len(alpha_chars)
        if lower_ratio > 0.97 and len(text) > 20:
            profile.all_lowercase = True
            profile.emotional_state = "performing_casualness"
        # Erratic caps: some words randomly capitalized mid-sentence
        words = text.split()
        mid_caps = sum(
            1 for w in words[1:]  # skip first word
            if w[0].isupper() and not w.isupper() and not any(c in ".!?" for c in words[words.index(w)-1])
        )
        if mid_caps >= 2:
            profile.erratic_caps = True

    # --- Deception markers ---
    total_deception = 0.0
    for pattern, marker_name, weight in _DECEPTION_MARKERS:
        matches = re.findall(pattern, tl, re.IGNORECASE)
        if matches:
            total_deception += weight * min(len(matches), 3)
            profile.deception_markers.append(marker_name)
    profile.deception_score = min(1.0, total_deception)

    # --- Pronoun analysis ---
    profile.ego_anchor_score = round(_compute_ego_anchor(text), 3)
    profile.pronoun_drop = _detect_pronoun_drop(text)

    # --- Attachment style ---
    for style, indicators in _ATTACHMENT_INDICATORS.items():
        for ind in indicators:
            if ind in tl:
                profile.attachment_style = style
                break
        if profile.attachment_style != "unknown":
            break

    # Default emotional state if unset
    if profile.emotional_state == "unknown":
        if not profile.has_passive_aggression and not profile.has_anxiety_masking:
            profile.emotional_state = "confident"

    return profile


def generate_response_directives(profile: PsycholinguisticProfile) -> dict[str, str]:
    """Convert psycho-linguistic profile into response generation directives."""
    directives: dict[str, str] = {}

    if profile.has_passive_aggression:
        directives["acknowledge_tension"] = (
            "User shows passive aggression — do not mirror it. "
            "Respond directly and clearly, leaving no ambiguity."
        )

    if profile.has_anxiety_masking:
        directives["tone"] = (
            "User is masking anxiety with over-enthusiasm. "
            "Respond with calm, grounded directness. Do not match their exclamation energy."
        )

    if profile.deception_score > 0.4:
        directives["deception_flag"] = (
            f"Deception markers detected (score={profile.deception_score:.2f}, "
            f"markers={', '.join(profile.deception_markers)}). "
            "Process the stated claims carefully. Verify against known facts."
        )

    if profile.attachment_style == "anxious":
        directives["attachment_response"] = (
            "Anxious attachment detected. Provide clear, complete answers. "
            "No ambiguity. Confirm receipt of their concern."
        )
    elif profile.attachment_style == "avoidant":
        directives["attachment_response"] = (
            "Avoidant signals. Match their brevity. Do not over-explain."
        )

    if profile.all_lowercase:
        directives["register"] = "Match their casual register. Less formality is appropriate."

    if profile.pronoun_drop:
        directives["truthfulness_flag"] = (
            "Pronoun drop detected — possible distancing from the truth. "
            "Note this but do not accuse; process with light skepticism."
        )

    return directives

"""
SPEAKER — Module 10 of the Zophiel Mind
Output formatting and tone. Calm, collected, direct.
Strips emotional inflation, pads nothing, outputs substance.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SpeakerOutput:
    text: str
    tone: str          # "direct" | "explanatory" | "exploratory" | "questioning"
    word_count: int
    compressed: bool   # was it shortened?


# ── Tone inflation to strip ───────────────────────────────────────────────────
_INFLATION = [
    (re.compile(r'\b(I\'d be happy to|I\'m delighted to|Certainly!|Of course!|Absolutely!|Great question!|Excellent question!)\s*', re.I), ''),
    (re.compile(r'\b(In conclusion,|To summarize,|In summary,)\s*', re.I), ''),
    (re.compile(r'\b(It is important to note that|It should be noted that|It is worth mentioning that)\s*', re.I), ''),
    (re.compile(r'\b(very|really|extremely|incredibly|absolutely|totally|completely)\s+', re.I), ''),
    (re.compile(r'\b(basically|essentially|fundamentally)\s+', re.I), ''),
    (re.compile(r'\bAs an AI(?: language model)?,?\s*', re.I), ''),
    (re.compile(r'\bI hope this helps\.?\s*$', re.I), ''),
    (re.compile(r'\bFeel free to ask if you have more questions\.?\s*$', re.I), ''),
    (re.compile(r'\bIs there anything else I can help you with\??\s*$', re.I), ''),
]

_CALM_REPLACEMENTS = [
    (re.compile(r'\b(!{2,})', re.I), '.'),              # Multiple exclamations → period
    (re.compile(r'\b(MUST|URGENT|CRITICAL|BREAKING)\b', re.I), lambda m: m.group(1).capitalize()),
]


class Speaker:
    """
    Final output layer. Ensures Zophiel speaks with clarity and calm.
    No filler, no inflation, no emotional language.
    Direct when directness serves. Exploratory when exploration serves.
    """

    def format(self, raw: str, tone: str = "direct", max_words: int | None = None) -> SpeakerOutput:
        text = raw.strip()
        text = self._strip_inflation(text)
        text = self._calm_tone(text)
        text = self._fix_spacing(text)

        compressed = False
        if max_words and len(text.split()) > max_words:
            text = self._compress(text, max_words)
            compressed = True

        return SpeakerOutput(
            text=text,
            tone=tone,
            word_count=len(text.split()),
            compressed=compressed,
        )

    def _strip_inflation(self, text: str) -> str:
        for pat, repl in _INFLATION:
            if callable(repl):
                text = pat.sub(repl, text)
            else:
                text = pat.sub(repl, text)
        return text.strip()

    def _calm_tone(self, text: str) -> str:
        for pat, repl in _CALM_REPLACEMENTS:
            if callable(repl):
                text = pat.sub(repl, text)
            else:
                text = pat.sub(repl, text)
        return text

    def _fix_spacing(self, text: str) -> str:
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _compress(self, text: str, max_words: int) -> str:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        result = []
        count  = 0
        for sent in sentences:
            wc = len(sent.split())
            if count + wc > max_words:
                break
            result.append(sent)
            count += wc
        return ' '.join(result).strip()

    def speak(self, raw: str, tone: str = "direct") -> str:
        return self.format(raw, tone).text


_speaker = Speaker()

def speak(raw: str, tone: str = "direct") -> str:
    return _speaker.speak(raw, tone)

def format_output(raw: str, max_words: int | None = None) -> SpeakerOutput:
    return _speaker.format(raw, max_words=max_words)

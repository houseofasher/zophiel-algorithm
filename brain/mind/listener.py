"""
LISTENER — Module 01 of the Zophiel Mind
Receives and normalises all incoming input: text, file paths, base64 data, voice transcripts.
Outputs a unified InputSignal object for downstream modules.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class InputSignal:
    raw: str                          # original input exactly as received
    text: str                         # normalised plain text
    modality: str                     # "text" | "file" | "voice" | "vision" | "data"
    metadata: dict[str, Any] = field(default_factory=dict)
    attachments: list[dict] = field(default_factory=list)  # [{type, content, name}]
    language: str = "en"
    confidence: float = 1.0


# ── Helpers ───────────────────────────────────────────────────────────────────

_URL_RE   = re.compile(r'https?://\S+', re.IGNORECASE)
_FILE_RE  = re.compile(r'(?:file|path|document|image|audio|video)\s*[:=]\s*(\S+)', re.IGNORECASE)
_B64_HEAD = re.compile(r'^data:([^;]+);base64,', re.IGNORECASE)

_TEXT_EXTS   = {'.txt','.md','.rst','.csv','.json','.xml','.html','.py','.js','.ts','.yaml','.yml'}
_IMAGE_EXTS  = {'.png','.jpg','.jpeg','.gif','.bmp','.webp','.svg'}
_AUDIO_EXTS  = {'.mp3','.wav','.ogg','.flac','.m4a','.opus'}
_DOC_EXTS    = {'.pdf','.docx','.xlsx','.pptx','.odt'}


def _detect_modality(raw: str) -> str:
    if _B64_HEAD.match(raw):
        mime = _B64_HEAD.match(raw).group(1)
        if mime.startswith('image'): return 'vision'
        if mime.startswith('audio'): return 'voice'
        return 'data'
    if os.path.exists(raw.strip()):
        ext = Path(raw.strip()).suffix.lower()
        if ext in _IMAGE_EXTS: return 'vision'
        if ext in _AUDIO_EXTS: return 'voice'
        return 'file'
    return 'text'


def _load_file_attachment(path: str) -> dict | None:
    p = Path(path.strip())
    if not p.exists():
        return None
    ext  = p.suffix.lower()
    name = p.name
    if ext in _TEXT_EXTS:
        try:
            content = p.read_text(encoding='utf-8', errors='replace')
            return {'type': 'text', 'name': name, 'content': content}
        except Exception:
            return None
    if ext in _IMAGE_EXTS:
        raw_bytes = p.read_bytes()
        b64 = base64.b64encode(raw_bytes).decode()
        mime = mimetypes.guess_type(str(p))[0] or 'image/png'
        return {'type': 'image', 'name': name, 'content': f'data:{mime};base64,{b64}'}
    if ext in _DOC_EXTS:
        return {'type': 'document', 'name': name, 'content': str(p)}
    return {'type': 'binary', 'name': name, 'content': str(p)}


def _extract_urls(text: str) -> list[str]:
    return _URL_RE.findall(text)


def _clean_text(raw: str) -> str:
    """Strip control chars, normalise whitespace."""
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


# ── Main API ──────────────────────────────────────────────────────────────────

class Listener:
    """
    Entry point for all input to the Zophiel Mind.
    Normalises diverse input types into a single InputSignal.
    """

    def receive(self, raw_input: str | dict | bytes) -> InputSignal:
        """
        Accept any of:
          - str  → plain text or base64-encoded media
          - dict → structured payload {text, files, modality, ...}
          - bytes → raw binary (treated as potential audio/image)
        Returns an InputSignal ready for the Understander.
        """
        if isinstance(raw_input, bytes):
            return self._from_bytes(raw_input)
        if isinstance(raw_input, dict):
            return self._from_dict(raw_input)
        return self._from_str(str(raw_input))

    # ── private ───────────────────────────────────────────────────────────────

    def _from_str(self, raw: str) -> InputSignal:
        modality   = _detect_modality(raw)
        attachments: list[dict] = []
        text       = raw

        if modality == 'file':
            att = _load_file_attachment(raw)
            if att:
                attachments.append(att)
                text = att.get('content', raw) if att['type'] == 'text' else f"[Attached {att['type']}: {att['name']}]"
        elif modality in ('vision', 'voice'):
            attachments.append({'type': modality, 'name': 'inline', 'content': raw})
            text = f"[{modality.upper()} input received]"
        else:
            # Look for file refs inside text
            for m in _FILE_RE.finditer(raw):
                att = _load_file_attachment(m.group(1))
                if att:
                    attachments.append(att)

        urls  = _extract_urls(raw)
        clean = _clean_text(text)

        return InputSignal(
            raw=raw,
            text=clean,
            modality=modality,
            metadata={'urls': urls, 'char_count': len(clean)},
            attachments=attachments,
        )

    def _from_dict(self, d: dict) -> InputSignal:
        text  = d.get('text', d.get('message', d.get('query', '')))
        modality = d.get('modality', 'text')
        files = d.get('files', [])
        attachments: list[dict] = []
        for f in files:
            if isinstance(f, str):
                att = _load_file_attachment(f)
                if att: attachments.append(att)
            elif isinstance(f, dict):
                attachments.append(f)
        return InputSignal(
            raw=json.dumps(d),
            text=_clean_text(str(text)),
            modality=modality,
            metadata=d.get('metadata', {}),
            attachments=attachments,
        )

    def _from_bytes(self, data: bytes) -> InputSignal:
        # Try to detect audio vs image by magic bytes
        if data[:4] in (b'RIFF', b'fLaC') or data[:3] == b'ID3':
            modality = 'voice'
        elif data[:8] in (b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff\xe0'):
            modality = 'vision'
        else:
            modality = 'data'
        b64 = base64.b64encode(data).decode()
        return InputSignal(
            raw='[binary]',
            text=f'[{modality.upper()} binary input, {len(data)} bytes]',
            modality=modality,
            attachments=[{'type': modality, 'name': 'binary', 'content': b64}],
        )


# ── Module-level singleton ────────────────────────────────────────────────────
_listener = Listener()

def listen(raw_input) -> InputSignal:
    return _listener.receive(raw_input)

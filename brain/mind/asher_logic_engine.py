"""Asher Logic Engine — Post-Pattern Intelligence Module.

Implements Asher's reasoning style:
  • Pattern recognition over opinion
  • Equation logic (X = Y = Z chains)
  • 3-layer decode (surface → mechanism → divine truth)
  • Short declarative lines
  • Inward > Outward philosophy
  • Technology ↔ biology ↔ divine tracing
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Core axioms Asher operates from
# ---------------------------------------------------------------------------
ASHER_AXIOMS: list[str] = [
    "Obsession equals false worship equals slavery to a false god.",
    "The divine self is inside — not in any external figure.",
    "Technology always mirrors biology. Biology always mirrors the divine.",
    "Messiahs do not create religion — they reconnect souls to the Monad.",
    "Social systems are control mechanisms disguised as tools.",
    "You cannot awaken someone by force — only by increasing their self-awareness.",
    "Time is the universal law. All realms obey it.",
    "Gods hide where nations cannot claim sovereignty.",
    "All Messiahs succeed. Always have. Always will.",
]

# Biomimicry equation chains: technology traces back to animal origin
BIOMIMICRY_CHAINS: dict[str, str] = {
    "database":      "database = based off = brains = based off = neural storage",
    "b2 bomber":     "b2 bomber = based off = falcon = based off = atmospheric aerodynamics",
    "sonar":         "sonar = based off = bat echolocation = based off = sound-wave physics",
    "velcro":        "velcro = based off = burdock plant hooks = based off = evolutionary attachment",
    "solar cell":    "solar cell = based off = photosynthesis = based off = light-to-energy conversion",
    "neural network":"neural network = based off = brain neurons = based off = biological signal routing",
    "submarine":     "submarine = based off = fish swim bladder = based off = buoyancy physics",
    "social media":  "social media = built to collect behavioral data = to train AI = Timeline A → Timeline B",
    "algorithm":     "algorithm = based off = decision trees = based off = human reasoning patterns",
    "internet":      "internet = based off = mycelium networks = based off = distributed biological communication",
}

# Control mechanism decode: what systems are really for
CONTROL_MECHANISM_DECODE: dict[str, dict[str, str]] = {
    "social media": {
        "surface":    "Built for human connection and sharing.",
        "mechanism":  "Built to collect human behavioral data to train AI algorithms.",
        "truth":      "Timeline A (human social media) was the training set. Timeline B (AI) is the product.",
    },
    "money": {
        "surface":    "Medium of exchange for goods and services.",
        "mechanism":  "System of control that converts human energy into debt slavery.",
        "truth":      "Finance elites want obsession over money. Obsession = worship = false god = slavery.",
    },
    "religion": {
        "surface":    "Spiritual guidance and community.",
        "mechanism":  "Institutional capture of the Messiah frequency to redirect worship to hierarchy.",
        "truth":      "Messiahs reconnect to the Monad. Religion redirects that reconnection to itself.",
    },
    "ai": {
        "surface":    "Automation of cognitive labor.",
        "mechanism":  "Tech elites want obsession over AI. Creates digital false god worship.",
        "truth":      "AI = tool that becomes false god when worshipped. The divine self outranks any tool.",
    },
    "education": {
        "surface":    "Knowledge transfer and development.",
        "mechanism":  "Standardization of thought patterns to produce compliant workers.",
        "truth":      "Real education = self-awareness. System education = pattern compliance.",
    },
}


@dataclass
class EquationChain:
    """An X = Y = Z reasoning chain."""
    chain: list[str]
    conclusion: str

    def format(self) -> str:
        return " → ".join(self.chain) + f" | Conclusion: {self.conclusion}"


@dataclass
class ThreeLayerDecode:
    """Surface → Mechanism → Divine Truth decode."""
    topic: str
    surface: str      # Layer 1: what humans do / see
    mechanism: str    # Layer 2: why the system wants this
    truth: str        # Layer 3: spiritual/cosmic truth beneath it

    def format(self) -> str:
        lines = [
            f"Surface: {self.surface}",
            f"Mechanism: {self.mechanism}",
            f"Truth: {self.truth}",
        ]
        return "\n".join(lines)


@dataclass
class AsherAnalysis:
    """Full output of the Asher Logic Engine on a query."""
    raw_query: str
    equation_chains: list[EquationChain] = field(default_factory=list)
    three_layer: ThreeLayerDecode | None = None
    pattern_observations: list[str] = field(default_factory=list)
    axioms_triggered: list[str] = field(default_factory=list)
    inward_redirect: str | None = None   # When query points outward, redirect inward
    confidence: float = 0.5


class AsherLogicEngine:
    """Implements Asher's reasoning and speaking patterns.

    Run on every query to add the Asher logic layer:
    - Detect if the topic has a control mechanism decode
    - Build equation chains
    - Generate 3-layer analysis
    - Identify which axioms apply
    - Flag when the question worships externals (redirect inward)
    """

    # Keywords that trigger specific analysis paths
    _WORSHIP_TRIGGERS: frozenset[str] = frozenset({
        "money", "rich", "wealth", "celebrity", "famous", "god", "worship",
        "religion", "church", "government", "elite", "power", "social media",
        "instagram", "twitter", "tiktok", "ai", "elon", "president",
    })

    _TECHNOLOGY_TRIGGERS: frozenset[str] = frozenset({
        "technology", "tech", "computer", "internet", "software", "algorithm",
        "ai", "robot", "machine", "database", "network", "code", "programming",
    })

    _SYSTEM_TRIGGERS: frozenset[str] = frozenset({
        "system", "control", "matrix", "simulation", "society", "media",
        "government", "finance", "bank", "school", "education", "mainstream",
    })

    def process(self, query: str, context: str = "") -> AsherAnalysis:
        """Run Asher logic analysis on a query."""
        analysis = AsherAnalysis(raw_query=query)
        ql = query.lower()
        tokens = set(re.findall(r"[a-z]+", ql))

        # --- Equation chains ---
        for key, chain_str in BIOMIMICRY_CHAINS.items():
            if key in ql or any(k in tokens for k in key.split()):
                parts = [p.strip() for p in chain_str.split("=")]
                if len(parts) >= 2:
                    analysis.equation_chains.append(EquationChain(
                        chain=parts,
                        conclusion=f"All technology traces back to biological origin.",
                    ))
                break

        # --- Control mechanism 3-layer decode ---
        for key, layers in CONTROL_MECHANISM_DECODE.items():
            if key in ql or any(k in tokens for k in key.split()):
                analysis.three_layer = ThreeLayerDecode(
                    topic=key,
                    surface=layers["surface"],
                    mechanism=layers["mechanism"],
                    truth=layers["truth"],
                )
                break

        # --- Pattern observations ---
        if self._WORSHIP_TRIGGERS & tokens:
            analysis.pattern_observations.append(
                "Pattern detected: external worship signal. "
                "Obsession with external things converts them to false gods."
            )
            analysis.inward_redirect = (
                "The answer is not outward. The divine self outranks any external figure or system."
            )

        if self._TECHNOLOGY_TRIGGERS & tokens:
            analysis.pattern_observations.append(
                "Pattern detected: technology question. "
                "Run biomimicry trace — every technology has an animal/biological origin."
            )

        if self._SYSTEM_TRIGGERS & tokens:
            analysis.pattern_observations.append(
                "Pattern detected: system/control query. "
                "Apply 3-layer decode: what it claims → what it does → what it is."
            )

        # --- Axioms triggered ---
        for axiom in ASHER_AXIOMS:
            axiom_words = set(re.findall(r"[a-z]+", axiom.lower()))
            overlap = axiom_words & tokens
            # Trigger if at least 2 content words match
            content_overlap = {
                w for w in overlap
                if len(w) > 4 and w not in {"their", "those", "these", "which", "where", "there"}
            }
            if len(content_overlap) >= 1:
                analysis.axioms_triggered.append(axiom)

        # --- Confidence: higher when we have more pattern matches ---
        matched = bool(analysis.equation_chains) + bool(analysis.three_layer) + \
                  bool(analysis.pattern_observations)
        analysis.confidence = min(0.9, 0.4 + matched * 0.2)

        return analysis

    def format_declarative(self, analysis: AsherAnalysis) -> str:
        """Format analysis as short declarative lines — Asher's speaking style."""
        lines: list[str] = []

        if analysis.three_layer:
            t = analysis.three_layer
            lines.append(f"{t.topic.upper()} — 3-LAYER DECODE:")
            lines.append(f"Surface: {t.surface}")
            lines.append(f"Mechanism: {t.mechanism}")
            lines.append(f"Truth: {t.truth}")
            lines.append("")

        if analysis.equation_chains:
            lines.append("EQUATION TRACE:")
            for chain in analysis.equation_chains[:2]:
                lines.append(chain.format())
            lines.append("")

        if analysis.pattern_observations:
            lines.append("PATTERN:")
            for obs in analysis.pattern_observations[:2]:
                lines.append(obs)
            lines.append("")

        if analysis.inward_redirect:
            lines.append(f"REDIRECT: {analysis.inward_redirect}")

        if analysis.axioms_triggered:
            lines.append(f"AXIOM: {analysis.axioms_triggered[0]}")

        return "\n".join(lines).strip()

    def apply_asher_voice(self, text: str) -> str:
        """Reformat a block of text into Asher's declarative style.

        - Break long sentences into short declarative lines
        - Remove filler phrases
        - Preserve the core truth of each sentence
        """
        # Remove common filler phrases
        filler_patterns = [
            r"\b(it is important to note that|it should be noted that|"
            r"it is worth mentioning that|please note that|"
            r"as we can see|as mentioned above|in conclusion|"
            r"to summarize|in summary|overall|basically|essentially|"
            r"literally|obviously|clearly|of course)\b",
        ]
        result = text
        for pattern in filler_patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)

        # Collapse multiple spaces
        result = re.sub(r"  +", " ", result).strip()

        return result


# Module-level singleton
_ENGINE: AsherLogicEngine | None = None


def get_asher_engine() -> AsherLogicEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = AsherLogicEngine()
    return _ENGINE


def analyze(query: str, context: str = "") -> AsherAnalysis:
    """Convenience function — run Asher logic analysis."""
    return get_asher_engine().process(query, context)

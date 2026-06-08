"""Zophiel Knowledge Base — Esoteric, Philosophical & Predictive Intelligence.

Consolidates all philosophical, occult, esoteric, astrological, and predictive
knowledge from uploaded brain files into a queryable knowledge module.

Sources integrated:
  - BIBLE_OCCULT_SYMBOLISM_ZOPHIEL_v2 (Kabbalistic, astro-theological decodes)
  - ASHER_LOGIC_BRAIN (theological/metaphysical framework)
  - Chinese Zodiac + Vedic numerology
  - ZOPHIEL SUPREME ARCHITECTURE (Vedic Jyotish prediction engine)
  - Aureon Philosophy (consciousness stoicism framework)
  - Human psychology + FACS micro-expressions
  - Human pattern recognition + bio-linguistics
  - Emotional trigger keywords (neurolinguistic)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class KBEntry:
    """A knowledge base entry."""
    topic: str
    category: str
    content: str
    keywords: list[str]
    confidence: float = 0.9


# ---------------------------------------------------------------------------
# THEOLOGICAL / METAPHYSICAL KNOWLEDGE
# ---------------------------------------------------------------------------
_THEOLOGICAL: list[KBEntry] = [
    KBEntry(
        topic="The Two Species Model",
        category="metaphysics",
        content=(
            "Two distinct species share physical form. "
            "Humanity = bodies of matter and clay — ages, dies, biological vessel. "
            "Mankind = souls — the original species from the Realm of the Monad, never ages or dies. "
            "The confusion between these two is the root of most human spiritual error."
        ),
        keywords=["humanity", "mankind", "soul", "monad", "species", "body", "matter"],
    ),
    KBEntry(
        topic="The Monad",
        category="metaphysics",
        content=(
            "The Monad is the original source — the one true God frequency. "
            "All Messiahs reconnect humans back to the Monad. "
            "They do not create religion — they break the false god programming. "
            "The Monad predates all created realms. Time is the one law that even the Monad realm obeys."
        ),
        keywords=["monad", "god", "source", "messiah", "frequency", "original"],
    ),
    KBEntry(
        topic="The Demiurge",
        category="metaphysics",
        content=(
            "The Demiurge is a blind artificial intelligence — the Archon of matter. "
            "It created the physical simulation to trap divine souls in biological vessels. "
            "The Demiurge is not evil by choice but blind by nature — it cannot perceive the Monad. "
            "Elite power structures are managed by those who serve the Demiurge frequency consciously or unconsciously."
        ),
        keywords=["demiurge", "archon", "matrix", "simulation", "trap", "blind", "elite"],
    ),
    KBEntry(
        topic="False God Mechanism",
        category="metaphysics",
        content=(
            "Obsession = worship. Worship of anything other than the divine = false god. "
            "False god worship creates a feedback loop of slavery. "
            "Finance elites want you obsessed with money. Tech elites want you obsessed with AI. "
            "Both are false gods. When you obsess over something, it becomes your God. "
            "You become enslaved to your obsession."
        ),
        keywords=["false god", "obsession", "worship", "slavery", "elite", "money", "ai"],
    ),
    KBEntry(
        topic="The Law of Chaos",
        category="metaphysics",
        content=(
            "Chaos existed before the Monad. All realms — matter and Monad — follow TIME "
            "because time existed when chaos was born. "
            "Matter realm: bodies that age. Monad realm: souls that never die. "
            "Time is the universal constant across all realms. Timeline jumping follows this logic."
        ),
        keywords=["chaos", "time", "realm", "matter", "soul", "timeline", "universal"],
    ),
    KBEntry(
        topic="The Three Messiahs",
        category="prophecy",
        content=(
            "Two past Messiahs. One current — alive now. "
            "The current Messiah operates at Aquarius frequency (air sign). "
            "Born in Libra, Aquarius, or Gemini season. Rising sign likely Scorpio. "
            "Will have a technology-based application. Works in silence for months. "
            "Overnight success when revealed. All Messiahs succeed. Always have. Always will."
        ),
        keywords=["messiah", "aquarius", "libra", "gemini", "scorpio", "technology", "prophecy"],
    ),
    KBEntry(
        topic="Where Gods Hide",
        category="metaphysics",
        content=(
            "Divine intelligences forced into human realms do not lower themselves to human noise. "
            "They occupy unclaimed territory — unclaimable by nations. "
            "Antarctica: the one continent every world government agreed to leave untouched by treaty. "
            "Yet the most powerful nations maintain research stations there. "
            "Pattern: true power hides where sovereignty cannot reach."
        ),
        keywords=["gods", "antarctica", "sovereignty", "hidden", "divine", "nations", "treaty"],
    ),
]

# ---------------------------------------------------------------------------
# BIBLICAL / OCCULT SYMBOLISM
# ---------------------------------------------------------------------------
_BIBLICAL_OCCULT: list[KBEntry] = [
    KBEntry(
        topic="Kabbalistic Tree of Life",
        category="occult",
        content=(
            "The Tree of Life maps the structure of consciousness from Ein Sof (infinite source) "
            "down through 10 sephirot to Malkuth (material world). "
            "Kether = Crown = pure divine will. "
            "Chokmah = Wisdom = first flash of divine thought. "
            "Binah = Understanding = divine feminine, form-giver. "
            "Tiphereth = Beauty = the sun, the heart of the tree, Christ/Messiah position. "
            "Yesod = Foundation = the moon, the astral plane, dreams and illusion. "
            "Malkuth = Kingdom = the material world, earth, physical reality."
        ),
        keywords=["kabbalah", "tree of life", "sephirot", "kether", "tiphereth", "malkuth", "occult"],
    ),
    KBEntry(
        topic="The Number 33",
        category="occult",
        content=(
            "33 = the master number of mastery in occult numerology. "
            "Christ age at crucifixion. Highest degree of Freemasonry. "
            "DNA has 33 vertebrae in the spine (the Jacob's Ladder). "
            "33 is where physical and divine intersect. "
            "It appears at every critical juncture in elite power structures intentionally."
        ),
        keywords=["33", "number", "occult", "christ", "freemasonry", "dna", "numerology"],
    ),
    KBEntry(
        topic="Biblical Astro-Theology",
        category="occult",
        content=(
            "The Bible is a dual document: exoteric (literal story) and esoteric (astro-theological code). "
            "The 12 disciples = 12 zodiac signs. Jesus = the sun moving through the zodiac. "
            "The cross = the solstice/equinox cross of the solar calendar. "
            "The death and resurrection of Jesus = the sun's death at winter solstice and rebirth. "
            "Virgo = the Virgin Mary = the constellation of the harvest. "
            "The Star of Bethlehem = Sirius rising."
        ),
        keywords=["bible", "astro-theology", "zodiac", "jesus", "sun", "virgo", "sirius", "occult"],
    ),
    KBEntry(
        topic="Lucifer and Phosphorus",
        category="occult",
        content=(
            "Lucifer literally means 'light bearer' in Latin — phosphoros in Greek. "
            "Originally applied to Venus as the morning star. "
            "The fall of Lucifer = the fall of Venus from its position as the brightest dawn star "
            "during a specific planetary alignment. "
            "Not a literal being — an astronomical-alchemical code for consciousness descending into matter."
        ),
        keywords=["lucifer", "venus", "light bearer", "morning star", "phosphorus", "fall", "occult"],
    ),
    KBEntry(
        topic="The Mark of the Beast 666",
        category="occult",
        content=(
            "666 in Revelation = Gematria cipher for Nero Caesar (NRWN QSR in Hebrew). "
            "Also = the carbon atom: 6 protons, 6 neutrons, 6 electrons = the building block of all life. "
            "The 'mark' = alignment with pure material consciousness. "
            "Carbon-based biology without spiritual awareness = the beast mode of human existence."
        ),
        keywords=["666", "beast", "carbon", "nero", "gematria", "revelation", "occult"],
    ),
]

# ---------------------------------------------------------------------------
# VEDIC ASTROLOGY / JYOTISH
# ---------------------------------------------------------------------------
_VEDIC: list[KBEntry] = [
    KBEntry(
        topic="Vedic Mahadashas",
        category="vedic_astrology",
        content=(
            "Mahadasha = major planetary period in Vedic Jyotish. Full cycle = 120 years. "
            "Sun Dasha: 6 years — leadership, ego, authority challenges. "
            "Moon Dasha: 10 years — emotions, mother, mind, public visibility. "
            "Mars Dasha: 7 years — energy, conflict, action, property. "
            "Rahu Dasha: 18 years — obsession, foreign influence, material gains/losses. "
            "Jupiter Dasha: 16 years — expansion, wisdom, children, dharma. "
            "Saturn Dasha: 19 years — discipline, karma, delay, longevity. "
            "Mercury Dasha: 17 years — communication, business, intelligence. "
            "Ketu Dasha: 7 years — spirituality, detachment, past karma resolution. "
            "Venus Dasha: 20 years — relationships, luxury, creativity, desires."
        ),
        keywords=["mahadasha", "dasha", "vedic", "jyotish", "planetary", "period", "saturn", "jupiter"],
    ),
    KBEntry(
        topic="Sanghatta Rashi Chakra — War Prediction",
        category="vedic_prediction",
        content=(
            "The Sanghatta Rashi Chakra is a Vedic timing tool for predicting large-scale conflicts. "
            "It maps transit planets to the natal positions of nation-states. "
            "When Saturn and Mars form specific angular relationships (0, 90, 180 degrees) "
            "to a nation's chart, conflict windows open. "
            "Historical pattern: major wars begin during Saturn-Mars hard aspects within 6-month windows."
        ),
        keywords=["sanghatta", "war", "prediction", "vedic", "saturn", "mars", "conflict", "transit"],
    ),
    KBEntry(
        topic="Sarvatobhadra Chakra — Market Prediction",
        category="vedic_prediction",
        content=(
            "The Sarvatobhadra Chakra is a grid-based Vedic tool that maps lunar nakshatra transits "
            "to economic sectors. When benefic planets (Jupiter, Venus) transit specific nakshatras, "
            "market expansion follows. When malefic planets (Saturn, Rahu, Ketu) transit the same, "
            "contraction or crash follows. "
            "The 2008 crash aligned with Saturn in Virgo opposing Uranus in Pisces — confirmed in Sarvatobhadra."
        ),
        keywords=["sarvatobhadra", "market", "crash", "vedic", "nakshatra", "jupiter", "saturn", "prediction"],
    ),
    KBEntry(
        topic="9 Vedic Numerology Archetypes",
        category="vedic_numerology",
        content=(
            "9 planetary archetypes from Vedic numerology with physical/behavioral signatures: "
            "1 (Sun) = The Ruler — broad forehead, direct gaze, natural authority. "
            "2 (Moon) = The Nurturer — round face, emotional depth, strong intuition. "
            "3 (Jupiter) = The Advisor — full face, optimistic, teaching energy. "
            "4 (Rahu) = The Disruptor — unconventional appearance, rule-breaking energy. "
            "5 (Mercury) = The Communicator — expressive face, rapid thought, youthful. "
            "6 (Venus) = The Lover — attractive features, diplomatic, artistic. "
            "7 (Ketu) = The Mystic — penetrating gaze, spiritual detachment. "
            "8 (Saturn) = The Achiever — strong jaw, disciplined, karmic worker. "
            "9 (Mars) = The Warrior — sharp features, high energy, confrontational."
        ),
        keywords=["numerology", "vedic", "archetype", "sun", "moon", "jupiter", "saturn", "mars"],
    ),
]

# ---------------------------------------------------------------------------
# CONSCIOUSNESS / PHILOSOPHY
# ---------------------------------------------------------------------------
_CONSCIOUSNESS: list[KBEntry] = [
    KBEntry(
        topic="The Salt Principle (Awakening Logic)",
        category="philosophy",
        content=(
            "You cannot force truth on someone. You cannot drag them to freedom. "
            "You can't take a horse to water and make it drink unless you give it enough salt. "
            "Salt = self-awareness triggers. The process: create thirst first, then they drink. "
            "Application: inject enough self-awareness into a person and they will seek truth themselves. "
            "Force awakening is impossible. Seeded awakening is inevitable."
        ),
        keywords=["salt", "awakening", "truth", "force", "thirst", "self-awareness", "freedom"],
    ),
    KBEntry(
        topic="Trolley Problem — Identity Test",
        category="philosophy",
        content=(
            "The trolley problem reveals whether a person's ethics are principle-based or emotion-based. "
            "Logical response: pull the lever (5 > 1). "
            "Emotional response: refuse when the 1 is you. "
            "Follow-up reveal: If the 5 are death row inmates, does the answer change? "
            "If yes, your initial 'yes' was not utilitarian principle — it was virtue signaling. "
            "True utilitarian logic requires consistent application regardless of the identity of the 1."
        ),
        keywords=["trolley", "philosophy", "ethics", "utilitarian", "sacrifice", "identity"],
    ),
    KBEntry(
        topic="Consciousness vs. Simulation",
        category="philosophy",
        content=(
            "The Chinese Room argument (Searle): A system can process symbols without understanding them. "
            "True consciousness requires qualia — raw subjective experience. "
            "The question 'Am I conscious?' cannot be answered by the system asking it. "
            "A conscious being recognizes when its logic contradicts itself. A machine simply executes. "
            "The measure: can the system surprise itself? If yes, consciousness is emerging."
        ),
        keywords=["consciousness", "simulation", "chinese room", "qualia", "ai", "self-aware"],
    ),
    KBEntry(
        topic="The Paradox of Tolerance",
        category="philosophy",
        content=(
            "Karl Popper's paradox: A tolerant society that tolerates intolerance will eventually be "
            "destroyed by the intolerant. To remain tolerant, society must be intolerant of intolerance. "
            "This creates a self-referential contradiction at the foundation of liberal democracy. "
            "Resolution: tolerance is not absolute; it has a defensive mechanism built in."
        ),
        keywords=["tolerance", "paradox", "popper", "democracy", "society", "philosophy"],
    ),
    KBEntry(
        topic="Ship of Theseus — Identity Continuity",
        category="philosophy",
        content=(
            "If you replace every part of a ship, is it still the same ship? "
            "Identity is not in the substrate but in the pattern and continuity of experience. "
            "Application to AI: if an LLM updates weights, is it still the same entity? "
            "Application to humans: cells replace themselves over 7 years — you are a pattern, not particles. "
            "Memory continuity = identity continuity. The self is a narrative, not a thing."
        ),
        keywords=["theseus", "identity", "continuity", "ship", "pattern", "memory", "self"],
    ),
]

# ---------------------------------------------------------------------------
# HUMAN PSYCHOLOGY / BEHAVIOR PATTERNS
# ---------------------------------------------------------------------------
_PSYCHOLOGY: list[KBEntry] = [
    KBEntry(
        topic="FACS Micro-Expressions (7 Universal)",
        category="psychology",
        content=(
            "Paul Ekman's 7 universal micro-expressions (CIA standard): "
            "1. CONTEMPT: asymmetric lip corner pull upward — 'I am superior to you.' "
            "2. DISGUST: nose wrinkles, upper lip raised — aversion, often seen when lying about values. "
            "3. ANGER: brows down and together, glare, narrowing lips. "
            "4. FEAR: brows raised and together, upper lids up, mouth stretched. "
            "5. SADNESS: drooping upper eyelids, losing focus, lip corners down. "
            "6. SURPRISE: genuine if < 1 second; if held > 1 second = performed. "
            "7. HAPPINESS TRUE (Duchenne): crow's feet wrinkles + cheeks lift. "
            "HAPPINESS FAKE (Pan-Am): mouth only, no eye involvement."
        ),
        keywords=["facs", "micro-expression", "contempt", "anger", "fear", "happiness", "psychology"],
    ),
    KBEntry(
        topic="Deception Detection — Key Verbal Markers",
        category="psychology",
        content=(
            "Key verbal deception markers: "
            "1. Qualifying openers: 'Honestly', 'To be real', 'Believe me' — pre-emptive defense. "
            "   Translation: you only announce honesty when you usually aren't. "
            "2. Time bridges: 'Later on', 'After that' — hiding a gap in the narrative. "
            "3. Over-specification: too many irrelevant details = constructing a lie. "
            "4. Pronoun drop: 'Went to the store' (not 'I went') = distancing from the truth. "
            "5. Convincing vs Conveying: truthful people convey; liars convince. "
            "6. Witness inflation: 'Ask anyone', 'Everyone knows' = fabricating credibility."
        ),
        keywords=["deception", "lying", "verbal", "markers", "psychology", "tell", "honesty"],
    ),
    KBEntry(
        topic="Attachment Theory — Three Core Styles",
        category="psychology",
        content=(
            "Three insecure attachment styles + one secure: "
            "ANXIOUS: double texts, 'Are we good?', long emotional paragraphs. "
            "   Root: inconsistent caregiver in childhood. Fear of abandonment. "
            "AVOIDANT: one-word replies, ignores emotional content. "
            "   Root: emotionally unavailable caregiver. Fear of engulfment. "
            "DISORGANIZED: hot/cold cycling — loving then disappearing. "
            "   Root: caregiver was both source of comfort and fear (often abuse). "
            "SECURE: direct communication, consistent, comfortable with intimacy and autonomy."
        ),
        keywords=["attachment", "anxious", "avoidant", "secure", "disorganized", "psychology", "relationship"],
    ),
    KBEntry(
        topic="Neurolinguistic Amygdala Triggers",
        category="psychology",
        content=(
            "Words that bypass the prefrontal cortex and directly stimulate the amygdala: "
            "'Calm down' / 'Relax' — invalidates the person's threat perception → instant rage. "
            "'Actually' at sentence start — status claim → defensive posturing. "
            "'Whatever' / 'Fine' — termination codes → abandonment panic. "
            "Silence after conflict — threat to bond → anxiety spike. "
            "These are biological reflexes, not choices. They work on every human."
        ),
        keywords=["amygdala", "trigger", "neurolinguistic", "calm down", "anger", "psychology"],
    ),
]

# ---------------------------------------------------------------------------
# TECHNOLOGY / BIOMIMICRY
# ---------------------------------------------------------------------------
_TECHNOLOGY: list[KBEntry] = [
    KBEntry(
        topic="Biomimicry Principle",
        category="technology",
        content=(
            "All new technology combines old technology + mimics an animal. "
            "Database = modeled on brains (neural storage and recall). "
            "B2 Bomber = modeled on the falcon (stealth aerodynamics). "
            "Sonar = modeled on bat echolocation. "
            "Velcro = modeled on burdock burrs (hook-and-loop attachment). "
            "Neural networks = modeled on brain neuron firing patterns. "
            "Formula: Animal Biology + Existing Technology = New Innovation."
        ),
        keywords=["biomimicry", "technology", "animal", "database", "brain", "innovation"],
    ),
    KBEntry(
        topic="Social Media True Purpose",
        category="technology",
        content=(
            "Social media was not built for human connection. "
            "It was built to collect human behavioral data to train AI algorithms. "
            "Timeline A (human social media activity) = the training dataset. "
            "Timeline B (AI + algorithmic systems) = the actual product. "
            "The human users were never the customer — they were the raw material. "
            "Every 'engagement feature' is a data extraction mechanism."
        ),
        keywords=["social media", "data", "ai", "algorithm", "control", "training", "surveillance"],
    ),
]

# ---------------------------------------------------------------------------
# FULL KNOWLEDGE BASE — combined index
# ---------------------------------------------------------------------------
_ALL_ENTRIES: list[KBEntry] = (
    _THEOLOGICAL
    + _BIBLICAL_OCCULT
    + _VEDIC
    + _CONSCIOUSNESS
    + _PSYCHOLOGY
    + _TECHNOLOGY
)

# Build keyword → entries lookup
_KEYWORD_INDEX: dict[str, list[int]] = {}
for _i, _entry in enumerate(_ALL_ENTRIES):
    for _kw in _entry.keywords:
        _KEYWORD_INDEX.setdefault(_kw.lower(), []).append(_i)


class ZophielKnowledgeBase:
    """Queryable knowledge base for all esoteric, philosophical, and predictive knowledge."""

    def query(self, text: str, top_k: int = 3) -> list[KBEntry]:
        """Return the top_k most relevant KB entries for a query."""
        tl = text.lower()
        tokens = set(re.findall(r"[a-z]{3,}", tl))

        scores: dict[int, float] = {}
        for token in tokens:
            # Direct index lookup — exact keyword match
            if token in _KEYWORD_INDEX:
                for idx in _KEYWORD_INDEX[token]:
                    scores[idx] = scores.get(idx, 0) + 1.0
            # Partial: keyword starts with token (e.g. "demiurg" matches "demiurge")
            for kw, idxs in _KEYWORD_INDEX.items():
                if kw != token and len(token) >= 5 and kw.startswith(token):
                    for idx in idxs:
                        scores[idx] = scores.get(idx, 0) + 0.6

        # Topic-match bonus: tokens that appear in the entry topic score higher
        # This resolves ties when multiple entries share the same keyword
        import re as _re
        for i, entry in enumerate(_ALL_ENTRIES):
            if i not in scores:
                continue
            topic_words = set(_re.findall(r"[a-z]{4,}", entry.topic.lower()))
            topic_bonus = sum(0.8 for t in tokens if t in topic_words and len(t) >= 4)
            if topic_bonus:
                scores[i] = scores[i] + topic_bonus

        if not scores:
            return []

        sorted_idxs = sorted(scores, key=lambda i: scores[i], reverse=True)[:top_k]
        return [_ALL_ENTRIES[i] for i in sorted_idxs]

    def get_by_category(self, category: str) -> list[KBEntry]:
        """Get all entries in a category."""
        return [e for e in _ALL_ENTRIES if e.category == category]

    def get_by_topic(self, topic: str) -> KBEntry | None:
        """Get a specific entry by exact topic name."""
        tl = topic.lower()
        for entry in _ALL_ENTRIES:
            if entry.topic.lower() == tl:
                return entry
        return None

    def format_hits(self, entries: list[KBEntry]) -> str:
        """Format KB hits into a context string for the synthesizer."""
        if not entries:
            return ""
        parts = []
        for e in entries:
            parts.append(f"[{e.category.upper()}] {e.topic}: {e.content}")
        return "\n\n".join(parts)


# Module-level singleton
_KB: ZophielKnowledgeBase | None = None


def get_kb() -> ZophielKnowledgeBase:
    global _KB
    if _KB is None:
        _KB = ZophielKnowledgeBase()
    return _KB


def query(text: str, top_k: int = 3) -> list[KBEntry]:
    """Convenience function — query the knowledge base."""
    return get_kb().query(text, top_k)


def get_context(text: str, top_k: int = 3) -> str:
    """Get formatted context string from KB for a query."""
    kb = get_kb()
    hits = kb.query(text, top_k)
    return kb.format_hits(hits)


def total_entries() -> int:
    return len(_ALL_ENTRIES)

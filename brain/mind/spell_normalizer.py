"""
Spell Normalizer — Tolerant human input processing.
Handles misspellings, typos, informal contractions, run-on words,
and casual language so the rest of the pipeline always gets clean text.
"""
from __future__ import annotations
import re
from difflib import get_close_matches

# Core vocabulary for fuzzy correction — domain terms + common words
_VOCAB = {
    # Common words
    "the","is","are","was","were","what","how","why","when","where","who",
    "does","do","did","can","could","would","should","will","have","has",
    "that","this","with","from","about","because","explain","define",
    "understand","difference","between","example","mean","means","work",
    "works","make","makes","cause","causes","effect","effects","result",
    # Science
    "entropy","quantum","physics","chemistry","biology","mathematics",
    "evolution","gravity","energy","momentum","thermodynamics","relativity",
    "electromagnetic","photon","electron","proton","neutron","atom","molecule",
    "protein","dna","rna","cell","gene","chromosome","mutation","enzyme",
    "climate","atmosphere","ecosystem","biodiversity","photosynthesis",
    "algorithm","neural","network","machine","learning","artificial",
    "intelligence","data","computer","software","hardware","programming",
    # Philosophy / humanities
    "philosophy","ethics","morality","consciousness","metaphysics","logic",
    "epistemology","categorical","imperative","utilitarian","virtue",
    "democracy","economics","capitalism","socialism","psychology","cognitive",
    "behavioral","sociology","anthropology","history","linguistics",
    # Medicine
    "immune","system","vaccine","antibody","infection","disease","cancer",
    "diabetes","metabolism","hormone","neuron","synapse","cortex","therapy",
    # Misc
    "actually","basically","essentially","specifically","generally",
    "algorithm","synthesize","analyze","analyze","define","describe",
}

_CONTRACTIONS = {
    "dont": "don't", "doesnt": "doesn't", "didnt": "didn't",
    "cant": "can't", "wont": "won't", "isnt": "isn't", "arent": "aren't",
    "wasnt": "wasn't", "werent": "weren't", "ive": "I've", "youve": "you've",
    "weve": "we've", "theyve": "they've", "im": "I'm", "youre": "you're",
    "theyre": "they're", "hes": "he's", "shes": "she's", "its": "it's",
    "thats": "that's", "whats": "what's", "hows": "how's", "wheres": "where's",
}

_INFORMAL = {
    "u": "you", "r": "are", "ur": "your", "pls": "please", "plz": "please",
    "thx": "thanks", "ty": "thank you", "bc": "because", "b4": "before",
    "btw": "by the way", "tbh": "to be honest", "imo": "in my opinion",
    "rn": "right now", "ngl": "not gonna lie", "idk": "I don't know",
    "smth": "something", "sth": "something", "cuz": "because",
    "gonna": "going to", "wanna": "want to", "gotta": "got to",
    "kinda": "kind of", "sorta": "sort of", "lol": "", "lmao": "",
}

def _fix_word(word: str) -> str:
    low = word.lower()
    # Informal substitutions
    if low in _INFORMAL:
        return _INFORMAL[low]
    # Contractions (no apostrophe)
    if low in _CONTRACTIONS:
        return _CONTRACTIONS[low]
    # Already a vocab word
    if low in _VOCAB:
        return word
    # Fuzzy match for words 5-12 chars; longer words are usually intentional
    if 5 <= len(low) <= 12:
        matches = get_close_matches(low, _VOCAB, n=1, cutoff=0.82)
        if matches:
            # Preserve original capitalisation
            fixed = matches[0]
            if word[0].isupper():
                fixed = fixed.capitalize()
            return fixed
    return word

def normalize(text: str) -> str:
    """
    Clean informal/misspelled user input into clean text.
    Preserves meaning and structure; only corrects likely errors.
    """
    if not text or not text.strip():
        return text

    # Collapse excessive whitespace and punctuation runs
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'([!?.,]){3,}', r'\1', text)

    # Split into tokens (words + punctuation)
    tokens = re.findall(r"[A-Za-z']+|[^A-Za-z']+", text)
    fixed_tokens = []
    for tok in tokens:
        if re.match(r"[A-Za-z']+", tok):
            fixed_tokens.append(_fix_word(tok))
        else:
            fixed_tokens.append(tok)

    result = ''.join(fixed_tokens)

    # Remove empty informal substitutions that left double spaces
    result = re.sub(r'  +', ' ', result).strip()

    return result

def normalize_query(text: str) -> tuple[str, bool]:
    """
    Returns (normalized_text, was_changed).
    """
    cleaned = normalize(text)
    return cleaned, (cleaned.lower() != text.lower())

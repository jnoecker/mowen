"""Porter stemmer event driver."""

from __future__ import annotations

import re

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet


def _stem(word: str) -> str:
    """Apply the Porter stemming algorithm to a single word.

    This is a faithful Python implementation of the original Porter (1980)
    algorithm.  It handles the five main steps of suffix stripping for
    English words.
    """
    if len(word) <= 2:
        return word

    def _is_consonant(w: str, i: int) -> bool:
        c = w[i]
        if c in "aeiou":
            return False
        if c == "y":
            return i == 0 or not _is_consonant(w, i - 1)
        return True

    def _measure(w: str) -> int:
        """Count the number of VC sequences (the 'measure' m)."""
        n = len(w)
        i = 0
        # Skip initial consonants
        while i < n and _is_consonant(w, i):
            i += 1
        m = 0
        while i < n:
            # Skip vowels
            while i < n and not _is_consonant(w, i):
                i += 1
            if i >= n:
                break
            # Skip consonants
            while i < n and _is_consonant(w, i):
                i += 1
            m += 1
        return m

    def _has_vowel(w: str) -> bool:
        return any(not _is_consonant(w, i) for i in range(len(w)))

    def _ends_double_consonant(w: str) -> bool:
        return len(w) >= 2 and w[-1] == w[-2] and _is_consonant(w, len(w) - 1)

    def _cvc(w: str) -> bool:
        n = len(w)
        if n < 3:
            return False
        return (_is_consonant(w, n - 3) and not _is_consonant(w, n - 2)
                and _is_consonant(w, n - 1) and w[-1] not in "wxy")

    def _replace(w: str, suffix: str, replacement: str, condition=None) -> tuple[str, bool]:
        if not w.endswith(suffix):
            return w, False
        stem = w[:-len(suffix)] if suffix else w
        if condition is None or condition(stem):
            return stem + replacement, True
        return w, False

    # Step 1a
    if word.endswith("sses"):
        word = word[:-2]
    elif word.endswith("ies"):
        word = word[:-2]
    elif not word.endswith("ss") and word.endswith("s"):
        word = word[:-1]

    # Step 1b
    if word.endswith("eed"):
        stem = word[:-3]
        if _measure(stem) > 0:
            word = word[:-1]
    else:
        changed = False
        for suffix in ("ed", "ing"):
            if word.endswith(suffix):
                stem = word[:-len(suffix)]
                if _has_vowel(stem):
                    word = stem
                    changed = True
                break
        if changed:
            if word.endswith("at") or word.endswith("bl") or word.endswith("iz"):
                word += "e"
            elif _ends_double_consonant(word) and word[-1] not in "lsz":
                word = word[:-1]
            elif _measure(word) == 1 and _cvc(word):
                word += "e"

    # Step 1c
    if word.endswith("y") and _has_vowel(word[:-1]):
        word = word[:-1] + "i"

    # Step 2
    step2 = [
        ("ational", "ate"), ("tional", "tion"), ("enci", "ence"),
        ("anci", "ance"), ("izer", "ize"), ("abli", "able"),
        ("alli", "al"), ("entli", "ent"), ("eli", "e"),
        ("ousli", "ous"), ("ization", "ize"), ("ation", "ate"),
        ("ator", "ate"), ("alism", "al"), ("iveness", "ive"),
        ("fulness", "ful"), ("ousness", "ous"), ("aliti", "al"),
        ("iviti", "ive"), ("biliti", "ble"),
    ]
    for suffix, replacement in step2:
        if word.endswith(suffix):
            stem = word[:-len(suffix)]
            if _measure(stem) > 0:
                word = stem + replacement
            break

    # Step 3
    step3 = [
        ("icate", "ic"), ("ative", ""), ("alize", "al"),
        ("iciti", "ic"), ("ical", "ic"), ("ful", ""), ("ness", ""),
    ]
    for suffix, replacement in step3:
        if word.endswith(suffix):
            stem = word[:-len(suffix)]
            if _measure(stem) > 0:
                word = stem + replacement
            break

    # Step 4
    step4 = [
        "al", "ance", "ence", "er", "ic", "able", "ible", "ant",
        "ement", "ment", "ent", "ion", "ou", "ism", "ate", "iti",
        "ous", "ive", "ize",
    ]
    for suffix in step4:
        if word.endswith(suffix):
            stem = word[:-len(suffix)]
            if suffix == "ion" and stem and stem[-1] in "st":
                if _measure(stem) > 1:
                    word = stem
            elif _measure(stem) > 1:
                word = stem
            break

    # Step 5a
    if word.endswith("e"):
        stem = word[:-1]
        m = _measure(stem)
        if m > 1 or (m == 1 and not _cvc(stem)):
            word = stem

    # Step 5b
    if _ends_double_consonant(word) and word[-1] == "l" and _measure(word) > 1:
        word = word[:-1]

    return word


@event_driver_registry.register("porter_stemmer")
class PorterStemmer(EventDriver):
    """Reduce words to their stems using the Porter stemming algorithm.

    Normalizes morphological variation so that "running", "runs", and
    "ran" all reduce to "run".  English only.
    """

    display_name = "Porter Stemmer"
    description = "Word stems via the Porter stemming algorithm (English)."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [TOKENIZER_PARAM]

    def create_event_set(self, text: str) -> EventSet:
        tok: str = self.get_param("tokenizer")
        events = EventSet()
        for word in tokenize_text(text, tok):
            stemmed = _stem(word.lower())
            if stemmed:
                events.append(Event(data=stemmed))
        return events

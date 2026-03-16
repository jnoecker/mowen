"""Syllable-based event drivers."""

from __future__ import annotations

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet

_VOWELS = frozenset("aeiouyAEIOUY")


def _count_syllables(word: str) -> int:
    """Count syllables using vowel-cluster heuristic (minimum 1)."""
    count = 0
    in_vowel = False
    for ch in word:
        if ch in _VOWELS:
            if not in_vowel:
                count += 1
                in_vowel = True
        else:
            in_vowel = False
    return max(count, 1)


@event_driver_registry.register("syllables_per_word")
class SyllablesPerWord(EventDriver):
    """Emit the syllable count of each word as an event.

    Uses a naive vowel-cluster counting heuristic.  Minimum count is 1.
    """

    display_name = "Syllables Per Word"
    description = "Syllable count per word (vowel-cluster heuristic)."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [TOKENIZER_PARAM]

    def create_event_set(self, text: str) -> EventSet:
        tok: str = self.get_param("tokenizer")
        return EventSet(
            Event(data=str(_count_syllables(w))) for w in tokenize_text(text, tok)
        )


@event_driver_registry.register("syllable_transitions")
class SyllableTransitions(EventDriver):
    """N-grams of syllable counts — captures rhythmic patterns.

    First counts syllables per word, then extracts sliding-window
    n-grams of the syllable count sequence.
    """

    display_name = "Syllable Transitions"
    description = "N-grams of syllable counts per word."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(name="n", description="N-gram size.", param_type=int, default=2, min_value=1, max_value=10),
            TOKENIZER_PARAM,
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        tok: str = self.get_param("tokenizer")
        syllables = [str(_count_syllables(w)) for w in tokenize_text(text, tok)]
        events = EventSet()
        for i in range(len(syllables) - n + 1):
            events.append(Event(data=" ".join(syllables[i:i + n])))
        return events

"""Leave-K-out N-gram event drivers."""

from __future__ import annotations

from itertools import combinations

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet


_PLACEHOLDER = "_"


def _leave_k_out(items: list[str], k: int) -> list[str]:
    """Generate all n-grams with k positions masked by a placeholder.

    For an n-gram ["a", "b", "c"] with k=1, produces:
    ["_ b c", "a _ c", "a b _"]
    """
    n = len(items)
    results = []
    for positions in combinations(range(n), k):
        masked = list(items)
        for pos in positions:
            masked[pos] = _PLACEHOLDER
        results.append(" ".join(masked))
    return results


@event_driver_registry.register("leave_k_out_character_ngram")
class LeaveKOutCharacterNGram(EventDriver):
    """Extract character n-grams with k positions masked.

    Generates all combinations of character n-grams where k character
    positions are replaced with a placeholder.  Captures partial
    patterns that are robust to minor spelling/OCR variation.
    """

    display_name = "Leave-K-Out Character N-gram"
    description = "Character n-grams with k positions masked."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(name="n", description="N-gram size.", param_type=int, default=3, min_value=2, max_value=10),
            ParamDef(name="k", description="Positions to leave out.", param_type=int, default=1, min_value=1, max_value=5),
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        k: int = self.get_param("k")
        if k >= n:
            return EventSet()
        events: list[Event] = []
        for i in range(len(text) - n + 1):
            chars = list(text[i:i + n])
            for masked in _leave_k_out(chars, k):
                events.append(Event(data=masked))
        return EventSet(events)


@event_driver_registry.register("leave_k_out_word_ngram")
class LeaveKOutWordNGram(EventDriver):
    """Extract word n-grams with k positions masked.

    Generates all combinations of word n-grams where k word positions
    are replaced with a placeholder.  Captures syntactic patterns
    independent of specific word choices.
    """

    display_name = "Leave-K-Out Word N-gram"
    description = "Word n-grams with k positions masked."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(name="n", description="N-gram size.", param_type=int, default=3, min_value=2, max_value=10),
            ParamDef(name="k", description="Positions to leave out.", param_type=int, default=1, min_value=1, max_value=5),
            TOKENIZER_PARAM,
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        k: int = self.get_param("k")
        tok: str = self.get_param("tokenizer")
        if k >= n:
            return EventSet()
        words = tokenize_text(text, tok)
        events: list[Event] = []
        for i in range(len(words) - n + 1):
            gram = list(words[i:i + n])
            for masked in _leave_k_out(gram, k):
                events.append(Event(data=masked))
        return EventSet(events)

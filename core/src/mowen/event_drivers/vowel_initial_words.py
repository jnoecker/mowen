"""Vowel-initial word event driver."""

from __future__ import annotations

from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry

_VOWELS = frozenset("aeiouAEIOU")


@event_driver_registry.register("vowel_initial_words")
class VowelInitialWords(EventDriver):
    """Emit words that begin with a vowel (a, e, i, o, u, case-insensitive)."""

    display_name = "Vowel-Initial Words"
    description = "Words that start with a vowel."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [TOKENIZER_PARAM]

    def create_event_set(self, text: str) -> EventSet:
        tok: str = self.get_param("tokenizer")
        return EventSet(
            Event(data=word) for word in tokenize_text(text, tok)
            if word and word[0] in _VOWELS
        )

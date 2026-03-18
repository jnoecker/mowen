"""Sorted n-gram event drivers for characters and words."""

from __future__ import annotations

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet


@event_driver_registry.register("sorted_character_ngram")
class SortedCharacterNGram(EventDriver):
    """Character n-grams with characters sorted alphabetically within each gram.

    Makes n-grams order-invariant — "abc" and "cba" produce the same event.
    """

    display_name = "Sorted Character N-Gram"
    description = "Alphabetically sorted character n-grams."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="n",
                description="N-gram size.",
                param_type=int,
                default=3,
                min_value=1,
                max_value=20,
            ),
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        return EventSet(
            Event(data="".join(sorted(text[i : i + n])))
            for i in range(len(text) - n + 1)
        )


@event_driver_registry.register("sorted_word_ngram")
class SortedWordNGram(EventDriver):
    """Word n-grams with words sorted alphabetically within each gram.

    Captures "bag of words within a window" regardless of word order.
    """

    display_name = "Sorted Word N-Gram"
    description = "Alphabetically sorted word n-grams."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="n",
                description="N-gram size.",
                param_type=int,
                default=2,
                min_value=1,
                max_value=10,
            ),
            TOKENIZER_PARAM,
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        tok: str = self.get_param("tokenizer")
        words = tokenize_text(text, tok)
        return EventSet(
            Event(data=" ".join(sorted(words[i : i + n])))
            for i in range(len(words) - n + 1)
        )

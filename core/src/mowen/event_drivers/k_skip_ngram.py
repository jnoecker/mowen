"""K-skip-N-gram event drivers for characters and words."""

from __future__ import annotations

from mowen.event_drivers.base import (
    EventDriver,
    event_driver_registry,
    generate_skip_ngrams,
)
from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import EventSet


@event_driver_registry.register("k_skip_character_ngram")
class KSkipCharacterNGram(EventDriver):
    """Character n-grams with K characters skipped between each selected character.

    For example, with N=2 and K=1, the text "abcd" produces "ac", "bd"
    in addition to the standard bigrams "ab", "bc", "cd".
    """

    display_name = "K-Skip Character N-Gram"
    description = "Character n-grams with K characters skipped between selections."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(name="n", description="N-gram size.", param_type=int, default=2, min_value=1, max_value=10),
            ParamDef(name="k", description="Characters to skip.", param_type=int, default=1, min_value=0, max_value=10),
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        k: int = self.get_param("k")
        return generate_skip_ngrams(text, n, k, joiner="")


@event_driver_registry.register("k_skip_word_ngram")
class KSkipWordNGram(EventDriver):
    """Word n-grams with K words skipped between each selected word."""

    display_name = "K-Skip Word N-Gram"
    description = "Word n-grams with K words skipped between selections."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(name="n", description="N-gram size.", param_type=int, default=2, min_value=1, max_value=10),
            ParamDef(name="k", description="Words to skip.", param_type=int, default=1, min_value=0, max_value=10),
            TOKENIZER_PARAM,
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        k: int = self.get_param("k")
        tok: str = self.get_param("tokenizer")
        return generate_skip_ngrams(tokenize_text(text, tok), n, k)

"""Punctuation n-gram event driver."""

from __future__ import annotations

import string

from mowen.event_drivers.base import EventDriver, event_driver_registry, generate_ngrams
from mowen.parameters import ParamDef
from mowen.types import EventSet


@event_driver_registry.register("punctuation_ngram")
class PunctuationNGram(EventDriver):
    """N-grams of punctuation characters — captures punctuation style.

    First extracts all punctuation characters from the text in order,
    then applies a sliding window of size *n* to produce n-grams.
    """

    display_name = "Punctuation N-Gram"
    description = "N-grams of consecutive punctuation marks."

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
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        punct_chars = [ch for ch in text if ch in string.punctuation]
        return generate_ngrams(punct_chars, n, joiner="")

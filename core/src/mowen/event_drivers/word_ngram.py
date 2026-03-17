"""Word n-gram event driver."""

from __future__ import annotations

from mowen.event_drivers.base import EventDriver, event_driver_registry, generate_ngrams
from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import EventSet


@event_driver_registry.register("word_ngram")
class WordNGram(EventDriver):
    """Extract overlapping word n-grams from text.

    The text is split using the configured tokenizer and a sliding
    window of size *n* moves one word at a time.
    """

    display_name = "Word N-Gram"
    description = "Extract word n-grams of configurable length."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="n",
                description="Number of words in each n-gram.",
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
        return generate_ngrams(tokenize_text(text, tok), n)

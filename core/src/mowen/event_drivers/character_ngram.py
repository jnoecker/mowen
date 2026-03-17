"""Character n-gram event driver."""

from __future__ import annotations

from mowen.parameters import ParamDef
from mowen.types import EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry, generate_ngrams


@event_driver_registry.register("character_ngram")
class CharacterNGram(EventDriver):
    """Extract overlapping character n-grams from text.

    A sliding window of size *n* moves one character at a time across the
    input, producing one :class:`~mowen.types.Event` per position.
    """

    display_name = "Character N-Gram"
    description = "Extract character n-grams of configurable length."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="n",
                description="Length of each character n-gram.",
                param_type=int,
                default=3,
                min_value=1,
                max_value=20,
            ),
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        return generate_ngrams(text, n, joiner="")

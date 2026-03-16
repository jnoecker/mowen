"""Word n-gram event driver."""

from __future__ import annotations

from mowen.parameters import ParamDef
from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry


@event_driver_registry.register("word_ngram")
class WordNGram(EventDriver):
    """Extract overlapping word n-grams from text.

    The text is split on whitespace and a sliding window of size *n* moves
    one word at a time, producing one :class:`~mowen.types.Event` per
    position.  The n-gram words are joined with a single space.
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
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        words = text.split()
        events = EventSet()
        for i in range(len(words) - n + 1):
            events.append(Event(data=" ".join(words[i : i + n])))
        return events

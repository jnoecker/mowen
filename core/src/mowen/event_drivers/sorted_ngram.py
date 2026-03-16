"""Sorted n-gram event drivers for characters and words."""

from __future__ import annotations

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
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
            ParamDef(name="n", description="N-gram size.", param_type=int, default=3, min_value=1, max_value=20),
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        events = EventSet()
        for i in range(len(text) - n + 1):
            gram = "".join(sorted(text[i:i + n]))
            events.append(Event(data=gram))
        return events


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
            ParamDef(name="n", description="N-gram size.", param_type=int, default=2, min_value=1, max_value=10),
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        words = text.split()
        events = EventSet()
        for i in range(len(words) - n + 1):
            gram = " ".join(sorted(words[i:i + n]))
            events.append(Event(data=gram))
        return events

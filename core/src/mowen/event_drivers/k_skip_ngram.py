"""K-skip-N-gram event drivers for characters and words."""

from __future__ import annotations

from itertools import combinations

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.types import Event, EventSet


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
        events = EventSet()
        step = k + 1
        for start in range(len(text)):
            indices = list(range(start, len(text), step))[:n]
            if len(indices) == n:
                events.append(Event(data="".join(text[i] for i in indices)))
        return events


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
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        k: int = self.get_param("k")
        words = text.split()
        events = EventSet()
        step = k + 1
        for start in range(len(words)):
            indices = list(range(start, len(words), step))[:n]
            if len(indices) == n:
                events.append(Event(data=" ".join(words[i] for i in indices)))
        return events

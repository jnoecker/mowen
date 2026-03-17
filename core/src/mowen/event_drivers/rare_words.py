"""Rare-word event driver."""

from __future__ import annotations

from collections import Counter

from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry


@event_driver_registry.register("rare_words")
class RareWords(EventDriver):
    """Emit words whose frequency falls within [min_count, max_count].

    By default emits hapax legomena (words appearing exactly once).
    Set *max_count* to 2 to also include dis legomena.
    """

    display_name = "Rare Words"
    description = "Words with low frequency in the text."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="min_count",
                description="Minimum occurrence count (inclusive).",
                param_type=int,
                default=1,
                min_value=1,
            ),
            ParamDef(
                name="max_count",
                description="Maximum occurrence count (inclusive).",
                param_type=int,
                default=1,
                min_value=1,
            ),
            TOKENIZER_PARAM,
        ]

    def create_event_set(self, text: str) -> EventSet:
        tok: str = self.get_param("tokenizer")
        min_c: int = self.get_param("min_count")
        max_c: int = self.get_param("max_count")
        words = tokenize_text(text, tok)
        counts = Counter(words)
        rare = {w for w, c in counts.items() if min_c <= c <= max_c}
        return EventSet(Event(data=w) for w in words if w in rare)

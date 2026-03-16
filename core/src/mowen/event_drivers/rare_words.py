"""Rare-word (hapax legomena) event driver."""

from __future__ import annotations

from collections import Counter

from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry


@event_driver_registry.register("rare_words")
class RareWords(EventDriver):
    """Emit words that appear exactly once in the text (hapax legomena).

    Events are produced in the order the words first appear.
    """

    display_name = "Rare Words"
    description = "Words that appear exactly once in the text."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [TOKENIZER_PARAM]

    def create_event_set(self, text: str) -> EventSet:
        tok: str = self.get_param("tokenizer")
        words = tokenize_text(text, tok)
        counts = Counter(words)
        hapaxes = {w for w, c in counts.items() if c == 1}
        return EventSet(Event(data=w) for w in words if w in hapaxes)

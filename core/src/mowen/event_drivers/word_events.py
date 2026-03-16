"""Word-level event driver."""

from __future__ import annotations

from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry


@event_driver_registry.register("word_events")
class WordEvents(EventDriver):
    """Split text into individual word events.

    Uses the configured tokenizer for word segmentation (default:
    whitespace).  Set ``tokenizer`` to ``"jieba"`` for Chinese text.
    """

    display_name = "Word Events"
    description = "Split text into word-level events."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [TOKENIZER_PARAM]

    def create_event_set(self, text: str) -> EventSet:
        tok: str = self.get_param("tokenizer")
        return EventSet(Event(data=word) for word in tokenize_text(text, tok))

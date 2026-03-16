"""Word-length event driver."""

from __future__ import annotations

from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry


@event_driver_registry.register("word_length")
class WordLength(EventDriver):
    """Emit the length of each word as an event."""

    display_name = "Word Length"
    description = "Create events from the length of each word."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [TOKENIZER_PARAM]

    def create_event_set(self, text: str) -> EventSet:
        tok: str = self.get_param("tokenizer")
        return EventSet(Event(data=str(len(word))) for word in tokenize_text(text, tok))

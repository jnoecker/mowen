"""Word-suffix event driver."""

from __future__ import annotations

from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry


@event_driver_registry.register("suffix")
class Suffix(EventDriver):
    """Extract the trailing *length* characters of each word as an event.

    Words shorter than *length* are skipped.
    """

    display_name = "Suffix"
    description = "Extract fixed-length word suffixes."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="length",
                description="Number of trailing characters to extract.",
                param_type=int,
                default=3,
                min_value=1,
                max_value=10,
            ),
            TOKENIZER_PARAM,
        ]

    def create_event_set(self, text: str) -> EventSet:
        length: int = self.get_param("length")
        tok: str = self.get_param("tokenizer")
        events = EventSet()
        for word in tokenize_text(text, tok):
            if len(word) >= length:
                events.append(Event(data=word[-length:]))
        return events

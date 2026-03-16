"""Line-level event drivers."""

from __future__ import annotations

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet


@event_driver_registry.register("line_length")
class LineLength(EventDriver):
    """Emit the word count of each line as an event.

    Useful for poetry, formatted text, and source code where line
    structure carries stylistic information.
    """

    display_name = "Line Length"
    description = "Word count per line."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [TOKENIZER_PARAM]

    def create_event_set(self, text: str) -> EventSet:
        tok: str = self.get_param("tokenizer")
        events = EventSet()
        for line in text.split("\n"):
            words = tokenize_text(line, tok)
            if words:
                events.append(Event(data=str(len(words))))
        return events


@event_driver_registry.register("new_lines")
class NewLines(EventDriver):
    """Emit each line of text as a separate event.

    Lines are split on newline characters.  Empty lines are skipped.
    """

    display_name = "New Lines"
    description = "Each line of text as an event."

    def create_event_set(self, text: str) -> EventSet:
        events = EventSet()
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped:
                events.append(Event(data=stripped))
        return events

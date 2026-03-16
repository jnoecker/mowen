"""Word-length event driver."""

from __future__ import annotations

from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry


@event_driver_registry.register("word_length")
class WordLength(EventDriver):
    """Emit the length of each whitespace-delimited word as an event."""

    display_name = "Word Length"
    description = "Create events from the length of each word."

    def create_event_set(self, text: str) -> EventSet:
        return EventSet(Event(data=str(len(word))) for word in text.split())

"""Word-level event driver."""

from __future__ import annotations

from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry


@event_driver_registry.register("word_events")
class WordEvents(EventDriver):
    """Split text on whitespace into individual word events."""

    display_name = "Word Events"
    description = "Split text into word-level events using whitespace."

    def create_event_set(self, text: str) -> EventSet:
        return EventSet(Event(data=word) for word in text.split())

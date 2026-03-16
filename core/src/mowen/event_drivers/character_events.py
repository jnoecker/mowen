"""Individual character event driver."""

from __future__ import annotations

from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry


@event_driver_registry.register("character_events")
class CharacterEvents(EventDriver):
    """Emit each character in the text as an individual event."""

    display_name = "Character Events"
    description = "Each character becomes a separate event."

    def create_event_set(self, text: str) -> EventSet:
        return EventSet(Event(data=ch) for ch in text)

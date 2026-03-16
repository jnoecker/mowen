"""Punctuation event driver."""

from __future__ import annotations

import string

from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry


@event_driver_registry.register("punctuation")
class Punctuation(EventDriver):
    """Emit each punctuation character in the text as an event."""

    display_name = "Punctuation"
    description = "Extract punctuation characters as events."

    def create_event_set(self, text: str) -> EventSet:
        return EventSet(
            Event(data=ch) for ch in text if ch in string.punctuation
        )

"""Punctuation event driver."""

from __future__ import annotations

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.types import Event, EventSet


def _is_punctuation(ch: str) -> bool:
    """Return True if *ch* is a punctuation or symbol character.

    Uses Unicode category awareness so that em-dashes, curly quotes,
    ellipsis characters, and other non-ASCII punctuation are captured
    — not just the 32 ASCII marks in :data:`string.punctuation`.
    """
    return not (ch.isalnum() or ch.isspace())


@event_driver_registry.register("punctuation")
class Punctuation(EventDriver):
    """Emit each punctuation character in the text as an event."""

    display_name = "Punctuation"
    description = "Extract punctuation characters as events."

    def create_event_set(self, text: str) -> EventSet:
        return EventSet(
            Event(data=ch) for ch in text if _is_punctuation(ch)
        )

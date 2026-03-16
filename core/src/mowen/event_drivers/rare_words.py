"""Rare-word (hapax legomena) event driver."""

from __future__ import annotations

from collections import Counter

from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry


@event_driver_registry.register("rare_words")
class RareWords(EventDriver):
    """Emit words that appear exactly once in the text (hapax legomena).

    Events are produced in the order the words first appear.
    """

    display_name = "Rare Words"
    description = "Words that appear exactly once in the text."

    def create_event_set(self, text: str) -> EventSet:
        words = text.split()
        counts = Counter(words)
        hapaxes = {w for w, c in counts.items() if c == 1}
        return EventSet(Event(data=w) for w in words if w in hapaxes)

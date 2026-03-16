"""Sentence-length event driver."""

from __future__ import annotations

import re

from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry


@event_driver_registry.register("sentence_length")
class SentenceLength(EventDriver):
    """Emit the word count of each sentence as an event.

    Sentences are delimited by one or more sentence-ending punctuation
    characters (``.``, ``!``, ``?``).  Empty sentences (e.g. from
    consecutive punctuation) are ignored.
    """

    display_name = "Sentence Length"
    description = "Word count per sentence as events."

    def create_event_set(self, text: str) -> EventSet:
        sentences = re.split(r"[.!?]+", text)
        events = EventSet()
        for sentence in sentences:
            words = sentence.split()
            if words:
                events.append(Event(data=str(len(words))))
        return events

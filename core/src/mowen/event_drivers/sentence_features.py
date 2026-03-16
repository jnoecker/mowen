"""Sentence-level event drivers."""

from __future__ import annotations

import re

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.types import Event, EventSet


@event_driver_registry.register("first_word_in_sentence")
class FirstWordInSentence(EventDriver):
    """Extract the first word of each sentence.

    Sentence-initial word choice is a strong stylistic signal in
    authorship attribution.
    """

    display_name = "First Word in Sentence"
    description = "First word of each sentence."

    def create_event_set(self, text: str) -> EventSet:
        events = EventSet()
        sentences = re.split(r"[.!?]+", text)
        for sentence in sentences:
            words = sentence.split()
            if words:
                events.append(Event(data=words[0]))
        return events


@event_driver_registry.register("sentence_events")
class SentenceEvents(EventDriver):
    """Emit whole sentences as events.

    Sentences are split on terminal punctuation (.!?).  Each sentence
    is stripped and emitted as a single event.
    """

    display_name = "Sentence Events"
    description = "Whole sentences as events."

    def create_event_set(self, text: str) -> EventSet:
        events = EventSet()
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence in sentences:
            s = sentence.strip()
            if s:
                events.append(Event(data=s))
        return events

"""Part-of-speech tag event driver using spaCy."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_drivers.base import SpacyEventDriver, event_driver_registry
from mowen.types import Event, EventSet


@event_driver_registry.register("pos_tags")
@dataclass
class POSTags(SpacyEventDriver):
    """Extract part-of-speech tags for each token using spaCy.

    Requires the ``spacy`` package and a downloaded language model (by
    default ``en_core_web_sm``).
    """

    display_name = "POS Tags"
    description = "Part-of-speech tags via spaCy."

    def create_event_set(self, text: str) -> EventSet:
        doc = self._get_nlp()(text)
        return EventSet(Event(data=token.pos_) for token in doc)

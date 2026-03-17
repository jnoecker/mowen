"""Named entity recognition event drivers using spaCy."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_drivers.base import SpacyEventDriver, event_driver_registry
from mowen.types import Event, EventSet


@event_driver_registry.register("named_entities")
@dataclass
class NamedEntities(SpacyEventDriver):
    """Extract named entity labels from text using spaCy NER.

    Emits entity labels (PERSON, ORG, GPE, DATE, etc.) for each
    recognized entity span.  Requires spaCy with a model that
    supports NER (e.g. ``en_core_web_sm``).
    """

    display_name = "Named Entities"
    description = "Named entity labels via spaCy NER."

    def create_event_set(self, text: str) -> EventSet:
        doc = self._get_nlp()(text)
        return EventSet(Event(data=ent.label_) for ent in doc.ents)


@event_driver_registry.register("entity_text")
@dataclass
class EntityText(SpacyEventDriver):
    """Extract the text of named entities from text using spaCy NER.

    Emits the actual entity text (e.g. "New York", "John Smith")
    rather than the label.  Useful for vocabulary-level analysis of
    entities an author references.
    """

    display_name = "Entity Text"
    description = "Named entity text spans via spaCy NER."

    def create_event_set(self, text: str) -> EventSet:
        doc = self._get_nlp()(text)
        return EventSet(Event(data=ent.text) for ent in doc.ents)


@event_driver_registry.register("entity_context")
@dataclass
class EntityContext(SpacyEventDriver):
    """Extract words before and after named entities.

    For each named entity, emits the word immediately before and
    the word immediately after the entity span.  Captures how an
    author introduces and follows up on named entities.
    """

    display_name = "Entity Context Words"
    description = "Words immediately before and after named entities."

    def create_event_set(self, text: str) -> EventSet:
        doc = self._get_nlp()(text)
        events = EventSet()
        for ent in doc.ents:
            if ent.start > 0:
                events.append(Event(data=f"BEFORE:{doc[ent.start - 1].text}"))
            if ent.end < len(doc):
                events.append(Event(data=f"AFTER:{doc[ent.end].text}"))
        return events

"""Named entity recognition event drivers using spaCy."""

from __future__ import annotations

from dataclasses import dataclass, field

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.types import Event, EventSet


@event_driver_registry.register("named_entities")
@dataclass
class NamedEntities(EventDriver):
    """Extract named entity labels from text using spaCy NER.

    Emits entity labels (PERSON, ORG, GPE, DATE, etc.) for each
    recognized entity span.  Requires spaCy with a model that
    supports NER (e.g. ``en_core_web_sm``).
    """

    display_name = "Named Entities"
    description = "Named entity labels via spaCy NER."

    _nlp: object = field(default=None, init=False, repr=False)
    _nlp_model_name: str = field(default="", init=False, repr=False)

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="model",
                description="spaCy language model to use.",
                param_type=str,
                default="en_core_web_sm",
            ),
        ]

    def create_event_set(self, text: str) -> EventSet:
        try:
            import spacy
        except ImportError as e:
            raise ImportError(
                "Named entity recognition requires spaCy. "
                "Install with: pip install 'mowen[nlp]'"
            ) from e

        model_name: str = self.get_param("model")
        if self._nlp is None or self._nlp_model_name != model_name:
            self._nlp = spacy.load(model_name)
            self._nlp_model_name = model_name
        doc = self._nlp(text)
        return EventSet(Event(data=ent.label_) for ent in doc.ents)


@event_driver_registry.register("entity_text")
@dataclass
class EntityText(EventDriver):
    """Extract the text of named entities from text using spaCy NER.

    Emits the actual entity text (e.g. "New York", "John Smith")
    rather than the label.  Useful for vocabulary-level analysis of
    entities an author references.
    """

    display_name = "Entity Text"
    description = "Named entity text spans via spaCy NER."

    _nlp: object = field(default=None, init=False, repr=False)
    _nlp_model_name: str = field(default="", init=False, repr=False)

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="model",
                description="spaCy language model to use.",
                param_type=str,
                default="en_core_web_sm",
            ),
        ]

    def create_event_set(self, text: str) -> EventSet:
        try:
            import spacy
        except ImportError as e:
            raise ImportError(
                "Named entity recognition requires spaCy. "
                "Install with: pip install 'mowen[nlp]'"
            ) from e

        model_name: str = self.get_param("model")
        if self._nlp is None or self._nlp_model_name != model_name:
            self._nlp = spacy.load(model_name)
            self._nlp_model_name = model_name
        doc = self._nlp(text)
        return EventSet(Event(data=ent.text) for ent in doc.ents)


@event_driver_registry.register("entity_context")
@dataclass
class EntityContext(EventDriver):
    """Extract words before and after named entities.

    For each named entity, emits the word immediately before and
    the word immediately after the entity span.  Captures how an
    author introduces and follows up on named entities.
    """

    display_name = "Entity Context Words"
    description = "Words immediately before and after named entities."

    _nlp: object = field(default=None, init=False, repr=False)
    _nlp_model_name: str = field(default="", init=False, repr=False)

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="model",
                description="spaCy language model to use.",
                param_type=str,
                default="en_core_web_sm",
            ),
        ]

    def create_event_set(self, text: str) -> EventSet:
        try:
            import spacy
        except ImportError as e:
            raise ImportError(
                "Named entity recognition requires spaCy. "
                "Install with: pip install 'mowen[nlp]'"
            ) from e

        model_name: str = self.get_param("model")
        if self._nlp is None or self._nlp_model_name != model_name:
            self._nlp = spacy.load(model_name)
            self._nlp_model_name = model_name
        doc = self._nlp(text)
        events = EventSet()
        for ent in doc.ents:
            if ent.start > 0:
                events.append(Event(data=f"BEFORE:{doc[ent.start - 1].text}"))
            if ent.end < len(doc):
                events.append(Event(data=f"AFTER:{doc[ent.end].text}"))
        return events

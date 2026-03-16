"""Part-of-speech tag event driver using spaCy."""

from __future__ import annotations

from mowen.parameters import ParamDef
from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry


@event_driver_registry.register("pos_tags")
class POSTags(EventDriver):
    """Extract part-of-speech tags for each token using spaCy.

    Requires the ``spacy`` package and a downloaded language model (by
    default ``en_core_web_sm``).
    """

    display_name = "POS Tags"
    description = "Part-of-speech tags via spaCy."

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

    _nlp: object = None
    _nlp_model_name: str = ""

    def create_event_set(self, text: str) -> EventSet:
        try:
            import spacy
        except ImportError as e:
            raise ImportError(
                "The 'spacy' package is required for the POS Tags event driver. "
                "Install it with: pip install spacy && python -m spacy download en_core_web_sm"
            ) from e

        model_name: str = self.get_param("model")
        if self._nlp is None or self._nlp_model_name != model_name:
            self._nlp = spacy.load(model_name)
            self._nlp_model_name = model_name
        doc = self._nlp(text)
        return EventSet(Event(data=token.pos_) for token in doc)

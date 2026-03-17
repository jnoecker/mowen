"""Base class for event drivers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field

from mowen.parameters import Configurable, ParamDef
from mowen.registry import Registry
from mowen.types import Event, EventSet, NumericEventSet


@dataclass
class EventDriver(ABC, Configurable):
    """Abstract base class for event drivers.

    An event driver transforms raw text into an :class:`~mowen.types.EventSet`
    -- the fundamental unit of stylistic evidence in the analysis pipeline.

    Subclasses must set ``display_name`` and ``description`` and implement
    :meth:`create_event_set`.
    """

    display_name: str = ""
    description: str = ""

    @abstractmethod
    def create_event_set(self, text: str) -> EventSet | NumericEventSet:
        """Transform *text* into an ordered sequence of events.

        Parameters
        ----------
        text:
            The (possibly canonicized) document text.

        Returns
        -------
        EventSet | NumericEventSet
            The events extracted from *text*.  Most drivers return a
            discrete :class:`EventSet`; embedding drivers return a
            :class:`NumericEventSet`.
        """


# --- spaCy base class ---

_SPACY_MODEL_PARAM = ParamDef(
    name="model",
    description="spaCy language model to use.",
    param_type=str,
    default="en_core_web_sm",
)


@dataclass
class SpacyEventDriver(EventDriver):
    """Base class for event drivers that use a spaCy language model.

    Handles lazy import of spaCy, model parameter declaration, and
    model caching so subclasses only need to implement
    :meth:`create_event_set` using :meth:`_get_nlp`.
    """

    _nlp: object = field(default=None, init=False, repr=False)
    _nlp_model_name: str = field(default="", init=False, repr=False)

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [_SPACY_MODEL_PARAM]

    def _get_nlp(self):
        """Return a cached spaCy language model, loading it on first use."""
        try:
            import spacy
        except ImportError as e:
            raise ImportError(
                "spaCy is required for this event driver. "
                "Install with: pip install 'mowen[nlp]'"
            ) from e
        model_name: str = self.get_param("model")
        if self._nlp is None or self._nlp_model_name != model_name:
            self._nlp = spacy.load(model_name)
            self._nlp_model_name = model_name
        return self._nlp


# --- N-gram helpers ---


def generate_ngrams(sequence: Sequence[str], n: int, joiner: str = " ") -> EventSet:
    """Build an EventSet of n-grams from *sequence* using a sliding window."""
    return EventSet(
        Event(data=joiner.join(sequence[i : i + n]))
        for i in range(len(sequence) - n + 1)
    )


def generate_skip_ngrams(
    sequence: Sequence[str], n: int, k: int, joiner: str = " ",
) -> EventSet:
    """Build an EventSet of k-skip-n-grams from *sequence*."""
    events = EventSet()
    step = k + 1
    for start in range(len(sequence)):
        indices = list(range(start, len(sequence), step))[:n]
        if len(indices) == n:
            events.append(Event(data=joiner.join(sequence[i] for i in indices)))
    return events


event_driver_registry: Registry[EventDriver] = Registry("event_driver")

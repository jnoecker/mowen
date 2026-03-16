"""Mosteller-Wallace function words event driver."""

from __future__ import annotations

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet


# The classic 70 function words from Mosteller & Wallace (1964),
# used in the landmark Federalist Papers authorship study.
_MW_WORDS: frozenset[str] = frozenset({
    "a", "all", "also", "an", "and", "any", "are", "as", "at",
    "be", "been", "but", "by",
    "can", "do", "down",
    "even", "every",
    "for", "from",
    "had", "has", "have", "her", "his", "however",
    "i", "if", "in", "into", "is", "it", "its",
    "may", "more", "must", "my",
    "no", "not", "now",
    "of", "on", "one", "only", "or", "our",
    "shall", "should", "so", "some", "such",
    "than", "that", "the", "then", "there", "things",
    "this", "to",
    "up", "upon",
    "was", "were", "what", "when", "which",
    "who", "will", "with", "would",
    "your",
})


@event_driver_registry.register("mw_function_words")
class MWFunctionWords(EventDriver):
    """Extract Mosteller-Wallace function words.

    Filters text to the 70 closed-class function words used in the
    classic Mosteller & Wallace (1964) Federalist Papers study.
    This is the most historically significant feature set in
    authorship attribution.
    """

    display_name = "Mosteller-Wallace Function Words"
    description = "The 70 function words from the Federalist Papers study."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [TOKENIZER_PARAM]

    def create_event_set(self, text: str) -> EventSet:
        tok: str = self.get_param("tokenizer")
        events = EventSet()
        for word in tokenize_text(text, tok):
            lower = word.lower()
            if lower in _MW_WORDS:
                events.append(Event(data=lower))
        return events

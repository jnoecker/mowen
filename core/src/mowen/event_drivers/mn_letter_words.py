"""M-N letter word event driver."""

from __future__ import annotations

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet


@event_driver_registry.register("mn_letter_words")
class MNLetterWords(EventDriver):
    """Emit words whose length falls between M and N (inclusive).

    Useful for isolating short function words, medium content words,
    or long technical vocabulary.
    """

    display_name = "M-N Letter Words"
    description = "Words with character length between M and N."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="m",
                description="Minimum word length (inclusive).",
                param_type=int,
                default=1,
                min_value=1,
                max_value=50,
            ),
            ParamDef(
                name="n",
                description="Maximum word length (inclusive).",
                param_type=int,
                default=3,
                min_value=1,
                max_value=50,
            ),
            TOKENIZER_PARAM,
        ]

    def create_event_set(self, text: str) -> EventSet:
        m: int = self.get_param("m")
        n: int = self.get_param("n")
        tok: str = self.get_param("tokenizer")
        events = EventSet()
        for word in tokenize_text(text, tok):
            if m <= len(word) <= n:
                events.append(Event(data=word))
        return events

"""Truncated (binned) frequency event driver."""

from __future__ import annotations

import math

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet


@event_driver_registry.register("truncated_frequency")
class TruncatedFrequency(EventDriver):
    """Bin words by their log-frequency within the document.

    Counts word frequencies in the document, then replaces each word
    with a discrete frequency bin (the integer part of its
    log2 frequency).  This reduces the feature space while preserving
    the author's preference for common vs. rare vocabulary.

    A word appearing 1 time -> bin "0", 2-3 times -> bin "1",
    4-7 times -> bin "2", 8-15 times -> bin "3", etc.
    """

    display_name = "Truncated Frequency"
    description = "Words replaced by log2 frequency bins."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [TOKENIZER_PARAM]

    def create_event_set(self, text: str) -> EventSet:
        tok: str = self.get_param("tokenizer")
        words = tokenize_text(text, tok)

        # Count frequencies.
        freq: dict[str, int] = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1

        # Map each word occurrence to its frequency bin.
        events: list[Event] = []
        for w in words:
            bin_label = str(int(math.log2(freq[w]))) if freq[w] > 0 else "0"
            events.append(Event(data=bin_label))
        return EventSet(events)

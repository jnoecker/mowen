"""Extreme culler — keep events appearing in all documents."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_cullers.base import EventCuller, _per_document_histograms, event_culler_registry
from mowen.types import Event, EventSet


@event_culler_registry.register("extreme")
@dataclass
class ExtremeCuller(EventCuller):
    """Keep only events that appear in every document.

    This ensures all retained features are universal across the corpus,
    eliminating document-specific vocabulary and focusing on shared
    stylistic elements.
    """

    display_name = "Extreme Culler"
    description = "Retains only events that appear in all documents."

    def init(self, event_sets: list[EventSet]) -> None:
        all_events, doc_histograms = _per_document_histograms(event_sets)
        if not all_events or not doc_histograms:
            self._kept_events = set()
            return

        n_docs = len(doc_histograms)
        self._kept_events = set()
        for event in all_events:
            present_in = sum(1 for h in doc_histograms if event in h)
            if present_in == n_docs:
                self._kept_events.add(event)

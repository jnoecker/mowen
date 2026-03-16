"""Index of dispersion event culler."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.event_cullers.base import EventCuller, _per_document_histograms, event_culler_registry
from mowen.parameters import ParamDef
from mowen.types import Event, EventSet


@event_culler_registry.register("index_of_dispersion")
@dataclass
class IndexOfDispersion(EventCuller):
    """Keep the top-*N* events ranked by index of dispersion (σ²/μ).

    The index of dispersion (variance-to-mean ratio) is useful for
    detecting overdispersed features — events whose frequency varies
    more than expected under a Poisson model.
    """

    display_name = "Index of Dispersion"
    description = "Retains the top N events by variance-to-mean ratio."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(name="n", description="Number of events to keep.", param_type=int, default=50, min_value=1),
        ]

    def init(self, event_sets: list[EventSet]) -> None:
        all_events, doc_histograms = _per_document_histograms(event_sets)
        if not all_events or not doc_histograms:
            self._kept_events = set()
            return

        n_docs = len(doc_histograms)
        event_iod: dict[Event, float] = {}
        for event in all_events:
            counts = [h.get(event, 0) for h in doc_histograms]
            mean = sum(counts) / n_docs
            if mean == 0.0:
                event_iod[event] = 0.0
                continue
            variance = sum((c - mean) ** 2 for c in counts) / n_docs
            event_iod[event] = variance / mean

        n: int = self.get_param("n")
        ranked = sorted(event_iod, key=lambda e: event_iod[e], reverse=True)
        self._kept_events = set(ranked[:n])

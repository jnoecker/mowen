"""Index of dispersion event culler."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_cullers.base import (
    EventCuller,
    _compute_event_stats,
    _per_document_histograms,
    _top_n_events,
    event_culler_registry,
)
from mowen.parameters import ParamDef
from mowen.types import EventSet


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
            ParamDef(
                name="n",
                description="Number of events to keep.",
                param_type=int,
                default=50,
                min_value=1,
            ),
        ]

    def init(self, event_sets: list[EventSet]) -> None:
        all_events, doc_histograms = _per_document_histograms(event_sets)
        if not all_events or not doc_histograms:
            self._kept_events = set()
            return

        stats = _compute_event_stats(all_events, doc_histograms)
        event_iod = {
            event: (st.variance / st.mean if st.mean != 0.0 else 0.0)
            for event, st in stats.items()
        }

        n: int = self.get_param("n")
        self._kept_events = _top_n_events(event_iod, n)

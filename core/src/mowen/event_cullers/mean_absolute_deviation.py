"""Mean absolute deviation event culler."""

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


@event_culler_registry.register("mean_absolute_deviation")
@dataclass
class MeanAbsoluteDeviation(EventCuller):
    """Keep the top-*N* events ranked by mean absolute deviation.

    MAD = (1/n) Σ|x_i - μ| measures the average spread of an event's
    frequency across documents.  Higher MAD indicates more variability,
    which tends to correlate with discriminative power.
    """

    display_name = "Mean Absolute Deviation"
    description = "Retains the top N events by mean absolute deviation of frequency."

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
        stats = _compute_event_stats(all_events, doc_histograms)
        event_mad = {
            event: sum(abs(c - st.mean) for c in st.counts) / n_docs
            for event, st in stats.items()
        }

        n: int = self.get_param("n")
        self._kept_events = _top_n_events(event_mad, n)

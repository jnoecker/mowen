"""Mean absolute deviation event culler."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_cullers.base import EventCuller, _per_document_histograms, event_culler_registry
from mowen.parameters import ParamDef
from mowen.types import Event, EventSet


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
        event_mad: dict[Event, float] = {}
        for event in all_events:
            counts = [h.get(event, 0) for h in doc_histograms]
            mean = sum(counts) / n_docs
            mad = sum(abs(c - mean) for c in counts) / n_docs
            event_mad[event] = mad

        n: int = self.get_param("n")
        ranked = sorted(event_mad, key=lambda e: event_mad[e], reverse=True)
        self._kept_events = set(ranked[:n])

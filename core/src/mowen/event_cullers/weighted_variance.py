"""Weighted variance event culler."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_cullers.base import EventCuller, _per_document_histograms, event_culler_registry
from mowen.parameters import ParamDef
from mowen.types import Event, EventSet


@event_culler_registry.register("weighted_variance")
@dataclass
class WeightedVariance(EventCuller):
    """Keep the top-*N* events ranked by weighted variance.

    Weighted variance uses each event's overall relative frequency as a
    weight: ``Var_w = Σ P_i (x_i - μ_w)²`` where ``μ_w = Σ P_i x_i``.
    This penalizes rare high-variance events relative to common ones.
    """

    display_name = "Weighted Variance"
    description = "Retains the top N events by frequency-weighted variance."

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
        # Total count across all documents for each event
        total_counts: dict[Event, int] = {}
        grand_total = 0
        for event in all_events:
            s = sum(h.get(event, 0) for h in doc_histograms)
            total_counts[event] = s
            grand_total += s

        event_wvar: dict[Event, float] = {}
        for event in all_events:
            if grand_total == 0:
                event_wvar[event] = 0.0
                continue
            p = total_counts[event] / grand_total  # overall relative frequency
            counts = [h.get(event, 0) for h in doc_histograms]
            weighted_mean = p * sum(counts) / n_docs
            weighted_var = sum(p * (c - weighted_mean) ** 2 for c in counts)
            event_wvar[event] = weighted_var

        n: int = self.get_param("n")
        ranked = sorted(event_wvar, key=lambda e: event_wvar[e], reverse=True)
        self._kept_events = set(ranked[:n])

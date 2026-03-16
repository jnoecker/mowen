"""Event culler that keeps events with coefficient of variation above a threshold."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.event_cullers.base import EventCuller, event_culler_registry
from mowen.parameters import ParamDef
from mowen.types import Event, EventSet


@event_culler_registry.register("coefficient_of_variation")
@dataclass
class CoefficientOfVariation(EventCuller):
    """Keep events whose coefficient of variation across documents exceeds a threshold.

    The coefficient of variation (CV) is defined as ``std_dev / mean``.
    Events with a higher CV have more variable frequency across documents,
    making them potentially more discriminating.

    During :meth:`init`, for each unique event the mean and standard
    deviation of its count across all event sets are computed.  Events
    with ``mean == 0`` are skipped.  Events whose CV is strictly greater
    than *min_cv* are retained.
    """

    display_name: str = "Coefficient of Variation"
    description: str = (
        "Retains events whose coefficient of variation (std_dev / mean) "
        "across documents exceeds the specified threshold."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="min_cv",
                description="Minimum coefficient of variation threshold (exclusive).",
                param_type=float,
                default=0.0,
                min_value=0.0,
            ),
        ]

    def init(self, event_sets: list[EventSet]) -> None:
        """Compute CV for each event across documents and select those above threshold."""
        all_events: set[Event] = set()
        doc_histograms: list[dict[Event, int]] = []
        for event_set in event_sets:
            counts = event_set.to_histogram().counts
            doc_histograms.append(counts)
            all_events.update(counts.keys())

        if not all_events or not doc_histograms:
            self._kept_events = set()
            return

        n_docs = len(doc_histograms)
        min_cv: float = self.get_param("min_cv")
        kept: set[Event] = set()

        for event in all_events:
            counts = [h.get(event, 0) for h in doc_histograms]
            mean = sum(counts) / n_docs
            if mean == 0.0:
                continue
            variance = sum((c - mean) ** 2 for c in counts) / n_docs
            std_dev = math.sqrt(variance)
            cv = std_dev / mean
            if cv > min_cv:
                kept.add(event)

        self._kept_events = kept

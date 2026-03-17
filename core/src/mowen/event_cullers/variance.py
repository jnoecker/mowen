"""Event culler that keeps events with cross-document frequency variance above a threshold."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_cullers.base import (
    EventCuller,
    _compute_event_stats,
    _per_document_histograms,
    event_culler_registry,
)
from mowen.parameters import ParamDef
from mowen.types import EventSet


@event_culler_registry.register("variance")
@dataclass
class Variance(EventCuller):
    """Keep events whose cross-document frequency variance exceeds a threshold.

    During :meth:`init`, for each unique event the variance of its count
    across all event sets is computed.  Events whose variance is strictly
    greater than *min_variance* are kept.
    """

    display_name: str = "Variance"
    description: str = (
        "Retains events whose cross-document frequency variance "
        "exceeds the specified threshold."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="min_variance",
                description="Minimum variance threshold (exclusive).",
                param_type=float,
                default=0.0,
                min_value=0.0,
            ),
        ]

    def init(self, event_sets: list[EventSet]) -> None:
        """Compute cross-document variance for each event and select those above threshold."""
        all_events, doc_histograms = _per_document_histograms(event_sets)

        if not all_events or not doc_histograms:
            self._kept_events = set()
            return

        min_variance: float = self.get_param("min_variance")
        stats = _compute_event_stats(all_events, doc_histograms)

        self._kept_events = {
            event for event, st in stats.items() if st.variance > min_variance
        }

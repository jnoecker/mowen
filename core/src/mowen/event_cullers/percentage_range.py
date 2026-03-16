"""Event culler that keeps events whose relative frequency falls within a percentage range."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_cullers.base import EventCuller, _aggregate_counts, event_culler_registry
from mowen.parameters import ParamDef
from mowen.types import EventSet


@event_culler_registry.register("percentage_range")
@dataclass
class PercentageRange(EventCuller):
    """Keep events whose corpus-wide relative frequency falls within a percentage range.

    During :meth:`init`, the relative frequency of every event across the
    entire corpus is computed.  During :meth:`cull`, only events whose
    relative frequency lies within ``[min_percent/100, max_percent/100]``
    are retained.
    """

    display_name: str = "Percentage Range"
    description: str = (
        "Retains events whose corpus-wide relative frequency falls "
        "within the specified percentage range."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="min_percent",
                description="Minimum relative frequency percentage (inclusive).",
                param_type=float,
                default=0.0,
                min_value=0.0,
                max_value=100.0,
            ),
            ParamDef(
                name="max_percent",
                description="Maximum relative frequency percentage (inclusive).",
                param_type=float,
                default=100.0,
                min_value=0.0,
                max_value=100.0,
            ),
        ]

    def init(self, event_sets: list[EventSet]) -> None:
        """Compute corpus-wide relative frequencies and select events in range."""
        combined = _aggregate_counts(event_sets)
        total = sum(combined.values())

        if total == 0:
            self._kept_events = set()
            return

        min_frac = self.get_param("min_percent") / 100.0
        max_frac = self.get_param("max_percent") / 100.0
        self._kept_events = {
            event
            for event, count in combined.items()
            if min_frac <= count / total <= max_frac
        }

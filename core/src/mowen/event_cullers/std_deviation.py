"""Event culler that keeps events within N standard deviations of the mean frequency."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.event_cullers.base import (
    EventCuller,
    _aggregate_counts,
    event_culler_registry,
)
from mowen.parameters import ParamDef
from mowen.types import EventSet


@event_culler_registry.register("std_deviation")
@dataclass
class StdDeviation(EventCuller):
    """Keep events whose corpus-wide frequency is within N standard deviations of the mean.

    During :meth:`init`, the total frequency of each unique event across all
    event sets is computed.  The mean and standard deviation of those
    frequencies are calculated, and events whose frequency falls within
    ``[mean - n*std_dev, mean + n*std_dev]`` are kept.
    """

    display_name: str = "Standard Deviation"
    description: str = (
        "Retains events whose corpus-wide frequency is within N "
        "standard deviations of the mean frequency."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="n",
                description="Number of standard deviations from the mean.",
                param_type=float,
                default=1.0,
                min_value=0.0,
            ),
        ]

    def init(self, event_sets: list[EventSet]) -> None:
        """Compute mean and std dev of event frequencies, select events in range."""
        combined = _aggregate_counts(event_sets)

        if not combined:
            self._kept_events = set()
            return

        frequencies = list(combined.values())
        mean = sum(frequencies) / len(frequencies)
        variance = sum((f - mean) ** 2 for f in frequencies) / len(frequencies)
        std_dev = math.sqrt(variance)

        n: float = self.get_param("n")
        lower = mean - n * std_dev
        upper = mean + n * std_dev
        self._kept_events = {
            event for event, freq in combined.items() if lower <= freq <= upper
        }

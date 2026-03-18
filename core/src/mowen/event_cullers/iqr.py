"""Event culler that removes frequency outliers using the IQR method."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_cullers.base import (
    EventCuller,
    _aggregate_counts,
    event_culler_registry,
)
from mowen.parameters import ParamDef
from mowen.types import EventSet


@event_culler_registry.register("iqr")
@dataclass
class IQR(EventCuller):
    """Keep events whose total frequency is not an outlier by the IQR method.

    During :meth:`init`, the total frequency per event across the corpus is
    computed.  Q1, Q3, and the IQR are calculated.  Events with frequency
    between ``Q1 - factor * IQR`` and ``Q3 + factor * IQR`` are retained.
    """

    display_name: str = "IQR Outlier Removal"
    description: str = (
        "Removes events whose corpus-wide frequency is an outlier "
        "according to the interquartile range method."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="factor",
                description="IQR multiplier for determining outlier bounds.",
                param_type=float,
                default=1.5,
                min_value=0.0,
            ),
        ]

    @staticmethod
    def _percentile(sorted_values: list[int], p: float) -> float:
        """Compute the p-th percentile (0-100) using linear interpolation."""
        n = len(sorted_values)
        if n == 0:
            return 0.0
        if n == 1:
            return float(sorted_values[0])
        k = (p / 100.0) * (n - 1)
        lo = int(k)
        hi = lo + 1
        if hi >= n:
            return float(sorted_values[-1])
        frac = k - lo
        return sorted_values[lo] + frac * (sorted_values[hi] - sorted_values[lo])

    def init(self, event_sets: list[EventSet]) -> None:
        """Compute IQR bounds and select non-outlier events."""
        combined = _aggregate_counts(event_sets)

        if not combined:
            self._kept_events = set()
            return

        frequencies = sorted(combined.values())
        q1 = self._percentile(frequencies, 25.0)
        q3 = self._percentile(frequencies, 75.0)
        iqr = q3 - q1

        factor: float = self.get_param("factor")
        lower = q1 - factor * iqr
        upper = q3 + factor * iqr

        self._kept_events = {
            event for event, freq in combined.items() if lower <= freq <= upper
        }

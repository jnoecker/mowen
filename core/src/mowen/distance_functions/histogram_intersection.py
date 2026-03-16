"""Distance function using histogram intersection with absolute frequencies."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("histogram_intersection")
@dataclass
class HistogramIntersectionDistance(DistanceFunction):
    """Histogram intersection distance (absolute frequencies).

    Computes 1 - (sum(min(h1[e], h2[e])) / min(total(h1), total(h2)))
    using absolute frequencies.  Returns 1.0 if either histogram is
    empty.
    """

    display_name: str = "Histogram Intersection Distance"
    description: str = (
        "Histogram intersection distance using absolute frequencies."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the histogram intersection distance between *h1* and *h2*."""
        total_h1 = h1.total
        total_h2 = h2.total

        if total_h1 == 0 or total_h2 == 0:
            return 1.0

        all_events = h1.unique_events() | h2.unique_events()

        intersection_sum = 0
        for event in all_events:
            intersection_sum += min(
                h1.absolute_frequency(event), h2.absolute_frequency(event)
            )

        min_total = min(total_h1, total_h2)
        return 1.0 - (intersection_sum / min_total)

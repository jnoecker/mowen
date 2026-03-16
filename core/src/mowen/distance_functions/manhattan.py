"""Distance function using Manhattan (city-block) distance."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("manhattan")
@dataclass
class ManhattanDistance(DistanceFunction):
    """Manhattan (city-block) distance.

    Computes the sum of absolute differences of relative frequencies
    over the union of all events present in either histogram.
    """

    display_name: str = "Manhattan Distance"
    description: str = (
        "Sum of absolute differences of relative frequencies (L1 norm)."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Manhattan distance between *h1* and *h2*."""
        all_events = h1.unique_events() | h2.unique_events()

        total = 0.0
        for event in all_events:
            total += abs(h1.relative_frequency(event) - h2.relative_frequency(event))

        return total

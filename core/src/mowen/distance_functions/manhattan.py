"""Distance function using Manhattan (city-block) distance."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import (
    DistanceFunction,
    _iter_relative_frequencies,
    distance_function_registry,
)
from mowen.types import Histogram


@distance_function_registry.register("manhattan")
@dataclass
class ManhattanDistance(DistanceFunction):
    """Manhattan (city-block) distance.

    Computes the sum of absolute differences of relative frequencies
    over the union of all events present in either histogram.
    """

    display_name: str = "Manhattan Distance"
    description: str = "Sum of absolute differences of relative frequencies (L1 norm)."

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Manhattan distance between *h1* and *h2*."""
        total = 0.0
        for freq1, freq2 in _iter_relative_frequencies(h1, h2):
            total += abs(freq1 - freq2)

        return total

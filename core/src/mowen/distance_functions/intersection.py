"""Distance function using intersection distance."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import (
    DistanceFunction,
    _iter_relative_frequencies,
    distance_function_registry,
)
from mowen.types import Histogram


@distance_function_registry.register("intersection")
@dataclass
class IntersectionDistance(DistanceFunction):
    """Intersection distance.

    Computes 1 - sum(min(p_i, q_i)) over the union of all events.
    The result lies between 0 and 1 for normalised histograms.
    """

    display_name: str = "Intersection Distance"
    description: str = (
        "One minus the sum of per-event minimum relative frequencies."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the intersection distance between *h1* and *h2*."""
        overlap = 0.0
        for freq1, freq2 in _iter_relative_frequencies(h1, h2):
            overlap += min(freq1, freq2)

        return 1.0 - overlap

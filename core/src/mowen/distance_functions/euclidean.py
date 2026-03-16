"""Distance function using Euclidean (L2) distance."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.distance_functions.base import (
    DistanceFunction,
    _iter_relative_frequencies,
    distance_function_registry,
)
from mowen.types import Histogram


@distance_function_registry.register("euclidean")
@dataclass
class EuclideanDistance(DistanceFunction):
    """Euclidean (L2) distance.

    Computes the square root of the sum of squared differences of
    relative frequencies over the union of all events present in
    either histogram.
    """

    display_name: str = "Euclidean Distance"
    description: str = (
        "Square root of the sum of squared differences of relative frequencies (L2 norm)."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Euclidean distance between *h1* and *h2*."""
        total = 0.0
        for freq1, freq2 in _iter_relative_frequencies(h1, h2):
            diff = freq1 - freq2
            total += diff * diff

        return math.sqrt(total)

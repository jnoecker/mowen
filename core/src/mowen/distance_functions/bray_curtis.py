"""Distance function using Bray-Curtis dissimilarity."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import (
    DistanceFunction,
    _iter_relative_frequencies,
    distance_function_registry,
)
from mowen.types import Histogram


@distance_function_registry.register("bray_curtis")
@dataclass
class BrayCurtisDistance(DistanceFunction):
    """Bray-Curtis dissimilarity.

    Computes sum(|p_i - q_i|) / sum(p_i + q_i) over the union of all
    events.  Returns 0.0 when the denominator is zero (both histograms
    are empty).
    """

    display_name: str = "Bray-Curtis Distance"
    description: str = "Bray-Curtis dissimilarity over relative frequencies."

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Bray-Curtis dissimilarity between *h1* and *h2*."""
        numerator = 0.0
        denominator = 0.0
        for p, q in _iter_relative_frequencies(h1, h2):
            numerator += abs(p - q)
            denominator += p + q

        if denominator == 0.0:
            return 0.0

        return numerator / denominator

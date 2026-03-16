"""Soergel distance."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, _iter_relative_frequencies, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("soergel")
@dataclass
class SoergelDistance(DistanceFunction):
    """Soergel distance.

    d = Σ|p_i - q_i| / Σ max(p_i, q_i)

    A normalized dissimilarity measure bounded in [0, 1].
    """

    display_name: str = "Soergel Distance"
    description: str = "Soergel distance: Σ|p-q| / Σmax(p,q)."

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Soergel distance between *h1* and *h2*."""
        numerator = 0.0
        denominator = 0.0
        for p, q in _iter_relative_frequencies(h1, h2):
            numerator += abs(p - q)
            denominator += max(p, q)
        if denominator == 0.0:
            return 0.0
        return numerator / denominator

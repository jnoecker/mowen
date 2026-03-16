"""Distance function using Chi-square distance."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import (
    DistanceFunction,
    _iter_relative_frequencies,
    distance_function_registry,
)
from mowen.types import Histogram


@distance_function_registry.register("chi_square")
@dataclass
class ChiSquareDistance(DistanceFunction):
    """Chi-square distance.

    Computes sum((p_i - q_i)^2 / q_i) for events where q_i > 0.
    Events where q_i == 0 are skipped.  Returns 0.0 if no valid events
    exist.
    """

    display_name: str = "Chi-Square Distance"
    description: str = (
        "Chi-square distance over relative frequencies."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Chi-square distance between *h1* and *h2*."""
        total = 0.0
        for p, q in _iter_relative_frequencies(h1, h2):
            if q > 0.0:
                diff = p - q
                total += (diff * diff) / q

        return total

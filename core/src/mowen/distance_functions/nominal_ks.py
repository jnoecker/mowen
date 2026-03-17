"""Nominal Kolmogorov-Smirnov distance."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import (
    DistanceFunction,
    _iter_relative_frequencies,
    distance_function_registry,
)
from mowen.types import Histogram


@distance_function_registry.register("nominal_ks")
@dataclass
class NominalKSDistance(DistanceFunction):
    """Nominal Kolmogorov-Smirnov distance.

    d = (1/2) Σ |p_i - q_i|

    A normalized variant of the Manhattan distance, bounded in [0, 1].
    Equivalent to half the L1 distance over relative frequencies.
    """

    display_name: str = "Nominal KS Distance"
    description: str = "Nominal Kolmogorov-Smirnov: (1/2)Σ|p-q|."

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the nominal KS distance between *h1* and *h2*."""
        total = 0.0
        for p, q in _iter_relative_frequencies(h1, h2):
            total += abs(p - q)
        return total / 2.0

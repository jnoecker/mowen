"""Weighted Euclidean Distance divergence."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, _iter_relative_frequencies, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("wed")
@dataclass
class WEDDistance(DistanceFunction):
    """Weighted Euclidean Distance divergence.

    d = √(Σ w_i (p_i - q_i)²)

    where w_i = p_i if p_i > 0, else 1.  This weights each dimension
    by the source frequency, giving more importance to events that the
    unknown document actually uses.
    """

    display_name: str = "Weighted Euclidean Distance"
    description: str = "WED: √(Σ w·(p-q)²), weighted by source frequency."

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the WED from *h1* to *h2*."""
        total = 0.0
        for p, q in _iter_relative_frequencies(h1, h2):
            w = p if p > 0.0 else 1.0
            total += w * (p - q) ** 2
        return math.sqrt(total)

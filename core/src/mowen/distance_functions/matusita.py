"""Matusita distance."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, _iter_relative_frequencies, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("matusita")
@dataclass
class MatusitaDistance(DistanceFunction):
    """Matusita distance.

    d = √(Σ(√p_i - √q_i)²)

    Related to Hellinger distance but without the 1/√2 normalization
    factor.  Bounded in [0, √2].
    """

    display_name: str = "Matusita Distance"
    description: str = "Matusita distance: √(Σ(√p - √q)²)."

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Matusita distance between *h1* and *h2*."""
        total = 0.0
        for p, q in _iter_relative_frequencies(h1, h2):
            diff = math.sqrt(p) - math.sqrt(q)
            total += diff * diff
        return math.sqrt(total)

"""Distance function using Bhattacharyya distance."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.distance_functions.base import (
    DistanceFunction,
    _iter_relative_frequencies,
    distance_function_registry,
)
from mowen.types import Histogram


@distance_function_registry.register("bhattacharyya")
@dataclass
class BhattacharyyaDistance(DistanceFunction):
    """Bhattacharyya distance.

    Computes -ln(BC) where BC = sum(sqrt(p_i * q_i)).  Returns
    ``float('inf')`` when BC <= 0 (no overlap).  BC is clamped to
    a maximum of 1.0 before taking the logarithm.
    """

    display_name: str = "Bhattacharyya Distance"
    description: str = (
        "Bhattacharyya distance: -ln of the Bhattacharyya coefficient."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Bhattacharyya distance between *h1* and *h2*."""
        bc = 0.0
        for p, q in _iter_relative_frequencies(h1, h2):
            bc += math.sqrt(p * q)

        if bc <= 0.0:
            return float("inf")

        # Clamp to handle floating-point rounding beyond 1.0.
        bc = min(bc, 1.0)
        return -math.log(bc)

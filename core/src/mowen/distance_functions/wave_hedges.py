"""Wave Hedges distance."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, _iter_relative_frequencies, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("wave_hedges")
@dataclass
class WaveHedgesDistance(DistanceFunction):
    """Wave Hedges distance.

    d = Σ(1 - min(p_i, q_i) / max(p_i, q_i))

    A ratio-based distance.  Each dimension contributes 0 (identical)
    to 1 (one is zero).  Terms where both values are zero contribute 0.
    """

    display_name: str = "Wave Hedges Distance"
    description: str = "Wave Hedges distance: Σ(1 - min/max)."

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Wave Hedges distance between *h1* and *h2*."""
        total = 0.0
        for p, q in _iter_relative_frequencies(h1, h2):
            mx = max(p, q)
            if mx > 0.0:
                total += 1.0 - min(p, q) / mx
        return total

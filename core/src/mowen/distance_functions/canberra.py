"""Distance function using Canberra distance."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("canberra")
@dataclass
class CanberraDistance(DistanceFunction):
    """Canberra distance.

    Computes sum(|p_i - q_i| / (|p_i| + |q_i|)) for events where the
    denominator is greater than zero.
    """

    display_name: str = "Canberra Distance"
    description: str = (
        "Canberra distance over relative frequencies."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Canberra distance between *h1* and *h2*."""
        all_events = h1.unique_events() | h2.unique_events()

        total = 0.0
        for event in all_events:
            p = h1.relative_frequency(event)
            q = h2.relative_frequency(event)
            denom = abs(p) + abs(q)
            if denom > 0.0:
                total += abs(p - q) / denom

        return total

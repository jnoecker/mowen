"""Stamatatos distance function."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("stamatatos")
@dataclass
class StamatatosDistance(DistanceFunction):
    """Stamatatos distance.

    Computes sum((2*(f(x)-g(x))/(f(x)+g(x)))^2) over all events.
    Events where both frequencies are zero are skipped.

    From: Stamatatos, "A Survey of Modern Authorship Attribution Methods"
    (JASIST, 2009).
    """

    display_name: str = "Stamatatos Distance"
    description: str = "Stamatatos profile-based distance: sum((2*(p-q)/(p+q))^2)."

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Stamatatos distance between *h1* and *h2*."""
        all_events = h1.unique_events() | h2.unique_events()
        if not all_events:
            return 0.0

        total = 0.0
        for event in all_events:
            p = h1.relative_frequency(event)
            q = h2.relative_frequency(event)
            denom = p + q
            if denom > 0.0:
                total += (2.0 * (p - q) / denom) ** 2

        return total

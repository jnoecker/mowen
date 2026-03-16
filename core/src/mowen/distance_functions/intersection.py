"""Distance function using intersection distance."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("intersection")
@dataclass
class IntersectionDistance(DistanceFunction):
    """Intersection distance.

    Computes 1 - sum(min(p_i, q_i)) over the union of all events.
    The result lies between 0 and 1 for normalised histograms.
    """

    display_name: str = "Intersection Distance"
    description: str = (
        "One minus the sum of per-event minimum relative frequencies."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the intersection distance between *h1* and *h2*."""
        all_events = h1.unique_events() | h2.unique_events()

        overlap = 0.0
        for event in all_events:
            overlap += min(
                h1.relative_frequency(event), h2.relative_frequency(event)
            )

        return 1.0 - overlap

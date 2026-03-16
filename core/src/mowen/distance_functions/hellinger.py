"""Distance function using Hellinger distance."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, distance_function_registry
from mowen.types import Histogram

_INV_SQRT2 = 1.0 / math.sqrt(2.0)


@distance_function_registry.register("hellinger")
@dataclass
class HellingerDistance(DistanceFunction):
    """Hellinger distance.

    Computes (1/sqrt(2)) * sqrt(sum((sqrt(p_i) - sqrt(q_i))^2)) over
    the union of all events in both histograms.
    """

    display_name: str = "Hellinger Distance"
    description: str = (
        "Hellinger distance over relative frequencies."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Hellinger distance between *h1* and *h2*."""
        all_events = h1.unique_events() | h2.unique_events()

        total = 0.0
        for event in all_events:
            diff = math.sqrt(h1.relative_frequency(event)) - math.sqrt(
                h2.relative_frequency(event)
            )
            total += diff * diff

        return _INV_SQRT2 * math.sqrt(total)

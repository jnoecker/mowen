"""Distance function using Hellinger distance."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.distance_functions.base import (
    DistanceFunction,
    _iter_relative_frequencies,
    distance_function_registry,
)
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
    description: str = "Hellinger distance over relative frequencies."

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Hellinger distance between *h1* and *h2*."""
        total = 0.0
        for freq1, freq2 in _iter_relative_frequencies(h1, h2):
            diff = math.sqrt(freq1) - math.sqrt(freq2)
            total += diff * diff

        return _INV_SQRT2 * math.sqrt(total)

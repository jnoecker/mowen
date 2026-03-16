"""Distance function using angular separation."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.distance_functions.base import (
    DistanceFunction,
    _cosine_similarity,
    distance_function_registry,
)
from mowen.types import Histogram


@distance_function_registry.register("angular_separation")
@dataclass
class AngularSeparationDistance(DistanceFunction):
    """Angular separation distance.

    Computes arccos(cosine_similarity) / pi.  The result is 0 when the
    vectors point in the same direction and 1 when they are anti-parallel.
    Returns 1.0 for zero vectors (maximally dissimilar).
    """

    display_name: str = "Angular Separation Distance"
    description: str = (
        "Angular separation: arccos(cosine similarity) / pi."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the angular separation distance between *h1* and *h2*."""
        sim = _cosine_similarity(h1, h2)
        if sim is None:
            return 1.0
        return math.acos(sim) / math.pi

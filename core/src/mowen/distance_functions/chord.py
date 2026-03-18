"""Distance function using chord distance."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.distance_functions.base import (
    DistanceFunction,
    _cosine_similarity,
    distance_function_registry,
)
from mowen.types import Histogram


@distance_function_registry.register("chord")
@dataclass
class ChordDistance(DistanceFunction):
    """Chord distance.

    Computes sqrt(2 * (1 - cosine_similarity)).  The cosine similarity
    is clamped to a maximum of 1.0.  Returns sqrt(2) for orthogonal
    vectors.
    """

    display_name: str = "Chord Distance"
    description: str = "Chord distance: sqrt(2 * (1 - cosine similarity))."

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the chord distance between *h1* and *h2*."""
        sim = _cosine_similarity(h1, h2)
        if sim is None:
            # Orthogonal / zero vectors => max chord distance.
            return math.sqrt(2.0)
        # Clamp similarity to max 1.0 for chord formula.
        sim = min(1.0, sim)
        return math.sqrt(2.0 * (1.0 - sim))

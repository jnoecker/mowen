"""Distance function using cosine distance."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import (
    DistanceFunction,
    _cosine_similarity,
    distance_function_registry,
)
from mowen.types import Histogram


@distance_function_registry.register("cosine")
@dataclass
class CosineDistance(DistanceFunction):
    """Cosine distance: 1 - cosine_similarity.

    Computes the cosine of the angle between two relative-frequency
    vectors and returns ``1 - cos(theta)``.  A result of 0 means the
    vectors point in the same direction (identical distributions); a
    result of 1 means they are orthogonal or at least one vector is
    zero.
    """

    display_name: str = "Cosine Distance"
    description: str = (
        "Cosine distance (1 - cosine similarity) over relative frequencies."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the cosine distance between *h1* and *h2*."""
        sim = _cosine_similarity(h1, h2)
        if sim is None:
            return 1.0
        return 1.0 - sim

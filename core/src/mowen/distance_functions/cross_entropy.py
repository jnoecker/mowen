"""Cross-entropy divergence distance."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.distance_functions.base import LOG_EPSILON, DistanceFunction, _iter_relative_frequencies, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("cross_entropy")
@dataclass
class CrossEntropyDistance(DistanceFunction):
    """Cross-entropy divergence.

    H(P, Q) = -Σ p(x) log(q(x))

    Measures the average number of bits needed to identify an event
    from P using the code optimized for Q.  Uses epsilon smoothing
    for events absent from Q.
    """

    display_name: str = "Cross Entropy"
    description: str = "Cross-entropy divergence: H(P, Q) = -Σ p(x) log q(x)."

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the cross-entropy from *h1* to *h2*."""
        total = 0.0
        for p, q in _iter_relative_frequencies(h1, h2):
            if p > 0.0:
                total -= p * math.log(q if q > 0.0 else LOG_EPSILON)
        return total

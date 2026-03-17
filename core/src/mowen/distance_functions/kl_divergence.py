"""Distance function using Kullback-Leibler divergence."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.distance_functions.base import LOG_EPSILON, DistanceFunction, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("kl_divergence")
@dataclass
class KLDivergence(DistanceFunction):
    """Kullback-Leibler divergence.

    Computes sum(p_i * log(p_i / q_i)) for events where p_i > 0.
    If p has events not present in q, a small epsilon (1e-10) is added
    to q values to avoid division by zero.  Returns 0.0 for empty
    histograms.
    """

    display_name: str = "KL Divergence"
    description: str = (
        "Kullback-Leibler divergence from h1 to h2 over relative frequencies."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the KL divergence from *h1* to *h2*."""
        all_events = h1.unique_events() | h2.unique_events()
        if not all_events:
            return 0.0

        total = 0.0
        for event in all_events:
            p = h1.relative_frequency(event)
            q = h2.relative_frequency(event)
            if p > 0.0:
                if q <= 0.0:
                    q = LOG_EPSILON
                total += p * math.log(p / q)

        return total

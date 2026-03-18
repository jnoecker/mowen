"""Distance function using Pearson correlation distance."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("pearson_correlation")
@dataclass
class PearsonCorrelationDistance(DistanceFunction):
    """Pearson correlation distance.

    Computes 1 - r where r is the Pearson correlation coefficient
    between the two relative-frequency vectors.  Returns 1.0 when
    either vector has zero standard deviation.
    """

    display_name: str = "Pearson Correlation Distance"
    description: str = "Pearson correlation distance: 1 - r over relative frequencies."

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Pearson correlation distance between *h1* and *h2*."""
        all_events = h1.unique_events() | h2.unique_events()
        n = len(all_events)
        if n == 0:
            return 1.0

        vals1 = [h1.relative_frequency(e) for e in all_events]
        vals2 = [h2.relative_frequency(e) for e in all_events]

        mean1 = sum(vals1) / n
        mean2 = sum(vals2) / n

        cov = 0.0
        var1 = 0.0
        var2 = 0.0
        for v1, v2 in zip(vals1, vals2):
            d1 = v1 - mean1
            d2 = v2 - mean2
            cov += d1 * d2
            var1 += d1 * d1
            var2 += d2 * d2

        std1 = math.sqrt(var1)
        std2 = math.sqrt(var2)

        if std1 == 0.0 or std2 == 0.0:
            return 1.0

        r = cov / (std1 * std2)
        return 1.0 - r

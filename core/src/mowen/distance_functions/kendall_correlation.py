"""Distance function using Kendall tau distance."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("kendall_correlation")
@dataclass
class KendallCorrelationDistance(DistanceFunction):
    """Kendall tau distance.

    Computes the Kendall rank-correlation coefficient tau from the
    relative-frequency vectors and returns (1 - tau) / 2 so that the
    result is normalised to [0, 1].  Returns 0.0 when fewer than two
    events are present.
    """

    display_name: str = "Kendall Correlation Distance"
    description: str = (
        "Kendall tau distance: (1 - tau) / 2 over relative frequencies."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Kendall tau distance between *h1* and *h2*."""
        all_events = sorted(
            h1.unique_events() | h2.unique_events(), key=str
        )
        n = len(all_events)
        if n < 2:
            return 0.0

        vals1 = [h1.relative_frequency(e) for e in all_events]
        vals2 = [h2.relative_frequency(e) for e in all_events]

        concordant = 0
        discordant = 0
        for i in range(n):
            for j in range(i + 1, n):
                diff1 = vals1[i] - vals1[j]
                diff2 = vals2[i] - vals2[j]
                product = diff1 * diff2
                if product > 0.0:
                    concordant += 1
                elif product < 0.0:
                    discordant += 1

        n_pairs = n * (n - 1) / 2.0
        tau = (concordant - discordant) / n_pairs
        return (1.0 - tau) / 2.0

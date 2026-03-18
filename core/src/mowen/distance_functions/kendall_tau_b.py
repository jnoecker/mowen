"""Distance function using Kendall tau-b rank correlation."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("kendall_tau_b")
@dataclass
class KendallTauBDistance(DistanceFunction):
    """Kendall tau-b distance.

    Like Kendall tau-a but corrected for ties.  Uses the formula:

        tau_b = (C - D) / sqrt((C + D + T1) * (C + D + T2))

    where C = concordant pairs, D = discordant pairs, T1 = ties in h1
    only, T2 = ties in h2 only.  Returns (1 - tau_b) / 2 normalised
    to [0, 1].

    Reference: Knight, "A Computer Method for Calculating Kendall's
    Tau with Ungrouped Data" (1966).
    """

    display_name: str = "Kendall Tau-B Distance"
    description: str = "Kendall tau-b distance: tie-corrected rank correlation."

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Kendall tau-b distance between *h1* and *h2*."""
        all_events = sorted(h1.unique_events() | h2.unique_events(), key=str)
        n = len(all_events)
        if n < 2:
            return 0.0

        vals1 = [h1.relative_frequency(e) for e in all_events]
        vals2 = [h2.relative_frequency(e) for e in all_events]

        concordant = 0
        discordant = 0
        ties1 = 0  # tied in h1 but not h2
        ties2 = 0  # tied in h2 but not h1

        for i in range(n):
            for j in range(i + 1, n):
                diff1 = vals1[i] - vals1[j]
                diff2 = vals2[i] - vals2[j]
                if diff1 == 0.0 and diff2 == 0.0:
                    continue  # joint tie — excluded from all counts
                elif diff1 == 0.0:
                    ties1 += 1
                elif diff2 == 0.0:
                    ties2 += 1
                elif (diff1 > 0.0) == (diff2 > 0.0):
                    concordant += 1
                else:
                    discordant += 1

        denom = math.sqrt(
            (concordant + discordant + ties1) * (concordant + discordant + ties2)
        )
        if denom == 0.0:
            return 0.0

        tau_b = (concordant - discordant) / denom
        return (1.0 - tau_b) / 2.0

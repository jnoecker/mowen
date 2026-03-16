"""Keselj weighted distance — AAAC 2004 winning metric."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("keselj_weighted")
@dataclass
class KeseljWeightedDistance(DistanceFunction):
    """Keselj weighted distance.

    The distance metric used by Keselj et al. (2003) which won the
    Ad-hoc Authorship Attribution Competition (AAAC) in 2004 when
    combined with character n-grams.

    For each event in the union of both histograms:
    ``((fa - fx) / (fa + fx))²``
    where *fa* and *fx* are the relative frequencies in each histogram.
    Events absent from one histogram contribute ``1.0``.
    """

    display_name: str = "Keselj Weighted Distance"
    description: str = (
        "Keselj weighted distance — the AAAC 2004 winning metric."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the Keselj weighted distance between *h1* and *h2*."""
        total = 0.0
        for event in h1.unique_events() | h2.unique_events():
            fa = h1.relative_frequency(event)
            fx = h2.relative_frequency(event)
            denom = fa + fx
            if denom > 0.0:
                total += ((fa - fx) / denom) ** 2
            # Both zero: impossible since event is from their union
        return total

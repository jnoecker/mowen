"""Normalized Compression Distance (NCD)."""

from __future__ import annotations

import gzip
from dataclasses import dataclass

from mowen.distance_functions.base import DistanceFunction, distance_function_registry
from mowen.types import Histogram


@distance_function_registry.register("ncd")
@dataclass
class NormalizedCompressionDistance(DistanceFunction):
    """Normalized Compression Distance.

    Measures similarity by comparing how well two texts compress
    together vs. separately:

        NCD(x, y) = (C(xy) - min(C(x), C(y))) / max(C(x), C(y))

    where C(x) is the compressed size of x.  Language-independent,
    requires no feature engineering.  Uses gzip (level 9).

    Note: operates on the raw text stored in the histogram's events,
    reconstructed as a space-joined string of event data.  For best
    results, use with ``word_events`` or ``character_events`` drivers.

    Reference: Cilibrasi & Vitanyi, "Clustering by Compression"
    (IEEE Trans. IT, 2005).  Halvani et al. (2016) for authorship
    attribution applications.
    """

    display_name: str = "Normalized Compression Distance"
    description: str = (
        "Compression-based distance: language-independent, no feature engineering."
    )

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the NCD between *h1* and *h2*."""
        # Reconstruct text from histogram events (frequency-weighted).
        tokens1 = []
        for event in h1.unique_events():
            tokens1.extend([event.data] * h1.absolute_frequency(event))
        tokens2 = []
        for event in h2.unique_events():
            tokens2.extend([event.data] * h2.absolute_frequency(event))

        text1 = " ".join(tokens1).encode("utf-8")
        text2 = " ".join(tokens2).encode("utf-8")

        if not text1 or not text2:
            return 1.0

        c1 = len(gzip.compress(text1, compresslevel=9))
        c2 = len(gzip.compress(text2, compresslevel=9))
        c12 = len(gzip.compress(text1 + b" " + text2, compresslevel=9))

        return (c12 - min(c1, c2)) / max(c1, c2)

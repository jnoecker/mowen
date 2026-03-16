"""Base distance function class and registry for histogram distance metrics."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

from mowen.parameters import Configurable
from mowen.registry import Registry
from mowen.types import Histogram


def _cosine_similarity(h1: Histogram, h2: Histogram) -> float | None:
    """Compute the cosine similarity between two histograms.

    Returns a value in ``[-1, 1]`` representing the cosine of the angle
    between the two relative-frequency vectors, or ``None`` if either
    histogram has zero magnitude (i.e. is a zero vector).
    """
    all_events = h1.unique_events() | h2.unique_events()

    dot_product = 0.0
    magnitude_h1 = 0.0
    magnitude_h2 = 0.0

    for event in all_events:
        freq1 = h1.relative_frequency(event)
        freq2 = h2.relative_frequency(event)
        dot_product += freq1 * freq2
        magnitude_h1 += freq1 * freq1
        magnitude_h2 += freq2 * freq2

    magnitude_h1 = math.sqrt(magnitude_h1)
    magnitude_h2 = math.sqrt(magnitude_h2)

    if magnitude_h1 == 0.0 or magnitude_h2 == 0.0:
        return None

    similarity = dot_product / (magnitude_h1 * magnitude_h2)
    # Clamp to handle floating-point rounding beyond [-1, 1].
    return max(-1.0, min(1.0, similarity))


@dataclass
class DistanceFunction(ABC, Configurable):
    """Abstract base class for all distance functions.

    A distance function measures the dissimilarity between two
    :class:`~mowen.types.Histogram` instances.  Subclasses must implement
    :meth:`distance` and set the ``display_name`` and ``description``
    class attributes.
    """

    display_name: str = ""
    description: str = ""

    @abstractmethod
    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Compute the distance between two histograms.

        Parameters
        ----------
        h1:
            The first histogram.
        h2:
            The second histogram.

        Returns
        -------
        float
            A non-negative distance value.  Zero indicates identical
            distributions.
        """


distance_function_registry: Registry[DistanceFunction] = Registry[DistanceFunction](
    "distance_function"
)

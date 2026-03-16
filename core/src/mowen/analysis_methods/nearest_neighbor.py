"""Nearest-neighbor analysis method."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.analysis_methods.base import NeighborAnalysisMethod, analysis_method_registry
from mowen.exceptions import PipelineError
from mowen.types import Attribution, Histogram


@analysis_method_registry.register("nearest_neighbor")
@dataclass
class NearestNeighbor(NeighborAnalysisMethod):
    """Attribute authorship by nearest-neighbor distance.

    For each known document, compute the distance from the unknown
    histogram to the known histogram.  Group by author and keep only the
    minimum distance per author.  Return results sorted by distance
    ascending (closest author first).

    Score semantics: lower = better match (distance-based).
    """

    display_name: str = "Nearest Neighbor"
    description: str = (
        "Assigns authorship based on the single closest known-author document."
    )

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions ranked by minimum distance per author."""
        if self.distance_function is None:
            raise PipelineError(
                "distance_function must be set before calling analyze()"
            )

        # Compute distance from unknown to every known document.
        best_per_author: dict[str, float] = {}
        for doc, hist in self._known_docs:
            author = doc.author or ""
            dist = self.distance_function.distance(unknown_histogram, hist)
            if author not in best_per_author or dist < best_per_author[author]:
                best_per_author[author] = dist

        # Build attributions sorted by distance ascending (closest first).
        attributions = [
            Attribution(author=author, score=dist)
            for author, dist in best_per_author.items()
        ]
        attributions.sort(key=lambda a: a.score)
        return attributions

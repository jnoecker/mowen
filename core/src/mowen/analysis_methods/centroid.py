"""Centroid-based analysis method."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.analysis_methods.base import CentroidAnalysisMethod, analysis_method_registry
from mowen.types import Document, Histogram


@analysis_method_registry.register("centroid")
@dataclass
class Centroid(CentroidAnalysisMethod):
    """Attribute authorship by distance to author centroids.

    For each author, build a single combined histogram by summing the
    counts of all that author's training documents.  At analysis time,
    compute the distance from the unknown histogram to each author's
    combined histogram and rank by distance ascending.

    Score semantics: lower = better match (distance-based).
    """

    display_name: str = "Centroid"
    description: str = (
        "Assigns authorship based on the distance to each author's "
        "centroid histogram (sum of all training document counts)."
    )

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Compute a centroid histogram per author by summing counts."""
        super().train(known_docs)
        author_event_sums, _ = self._accumulate_author_events(self._known_docs)

        self._centroids = {
            author: Histogram(counts)
            for author, counts in author_event_sums.items()
        }

"""Absolute-centroid analysis method."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from mowen.analysis_methods.base import CentroidAnalysisMethod, analysis_method_registry
from mowen.types import Document, Event, Histogram


@analysis_method_registry.register("absolute_centroid")
@dataclass
class AbsoluteCentroid(CentroidAnalysisMethod):
    """Attribute authorship by distance to author absolute-frequency centroids.

    For each author, compute the mean absolute frequency of each event
    across all that author's training documents to form a centroid
    histogram.  At analysis time, compute the distance from the unknown
    histogram to each centroid and rank by distance ascending.

    Score semantics: lower = better match (distance-based).
    """

    display_name: str = "Absolute Centroid"
    description: str = (
        "Assigns authorship based on the distance to each author's "
        "centroid histogram (mean absolute frequencies)."
    )

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Compute a centroid histogram per author by averaging absolute counts."""
        super().train(known_docs)

        # Collect all events and counts per author, and document counts.
        author_event_sums: dict[str, dict[Event, int]] = defaultdict(dict)
        author_doc_counts: dict[str, int] = defaultdict(int)

        for doc, hist in self._known_docs:
            author = doc.author or ""
            author_doc_counts[author] += 1
            for event in hist.unique_events():
                count = hist.absolute_frequency(event)
                author_event_sums[author][event] = (
                    author_event_sums[author].get(event, 0) + count
                )

        # Build centroid histograms using mean counts (rounded to int for Histogram).
        self._centroids = {}
        for author, event_sums in author_event_sums.items():
            n_docs = author_doc_counts[author]
            mean_counts: dict[Event, int] = {
                event: round(total / n_docs)
                for event, total in event_sums.items()
            }
            self._centroids[author] = Histogram(mean_counts)

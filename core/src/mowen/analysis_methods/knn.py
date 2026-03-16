"""K-nearest-neighbors (KNN) analysis method."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from mowen.analysis_methods.base import NeighborAnalysisMethod, analysis_method_registry
from mowen.exceptions import PipelineError
from mowen.parameters import ParamDef
from mowen.types import Attribution, Histogram


@analysis_method_registry.register("knn")
@dataclass
class KNearestNeighbors(NeighborAnalysisMethod):
    """Attribute authorship by K-nearest-neighbor voting.

    Compute the distance from the unknown histogram to every known
    document histogram.  Take the *k* nearest neighbors and count votes
    per author among those neighbors.  Score is ``vote_count / k``.

    Score semantics: higher = better match (vote-fraction-based).
    """

    display_name: str = "K-Nearest Neighbors"
    description: str = (
        "Assigns authorship by majority vote among the k closest "
        "known-author documents."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        """Declare the *k* parameter."""
        return [
            ParamDef(
                name="k",
                description="Number of nearest neighbors to consider.",
                param_type=int,
                default=5,
                min_value=1,
            ),
        ]

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions ranked by vote fraction among k neighbors."""
        if self.distance_function is None:
            raise PipelineError(
                "distance_function must be set before calling analyze()"
            )

        k: int = self.get_param("k")

        # Compute distance from unknown to every known document.
        distances: list[tuple[str, float]] = []
        for doc, hist in self._known_docs:
            author = doc.author or ""
            dist = self.distance_function.distance(unknown_histogram, hist)
            distances.append((author, dist))

        # Sort by distance ascending and take the k nearest.
        distances.sort(key=lambda pair: pair[1])
        neighbors = distances[:k]
        actual_k = len(neighbors)

        # Count votes per author.
        votes: Counter[str] = Counter(author for author, _ in neighbors)

        # Build attributions scored by vote_count / actual_k, sorted descending.
        # Use actual_k (not requested k) so scores always sum to 1.0
        # even when fewer documents are available than k.
        attributions = [
            Attribution(author=author, score=count / actual_k)
            for author, count in votes.items()
        ]
        attributions.sort(key=lambda a: a.score, reverse=True)
        return attributions

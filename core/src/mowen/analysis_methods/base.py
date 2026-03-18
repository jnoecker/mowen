"""Base analysis method class and registry for authorship attribution methods."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field

from mowen.distance_functions.base import DistanceFunction
from mowen.exceptions import PipelineError
from mowen.parameters import Configurable
from mowen.registry import Registry
from mowen.types import Attribution, Document, Event, Histogram


@dataclass
class AnalysisMethod(ABC, Configurable):
    """Abstract base class for all analysis methods.

    An analysis method takes histograms from known-author documents and
    an unknown-author histogram, then produces a ranked list of
    :class:`~mowen.types.Attribution` results.  Subclasses must implement
    :meth:`analyze` and set the ``display_name`` and ``description``
    class attributes.

    Score semantics vary by method family:

    * **Distance-based** methods: lower score = better match.
    * **Probability-based** methods: higher score = better match.
    """

    display_name: str = ""
    description: str = ""
    lower_is_better: bool = True

    _known_docs: list[tuple[Document, Histogram]] = field(
        default_factory=list,
        init=False,
        repr=False,
    )

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Store training data for later analysis.

        Parameters
        ----------
        known_docs:
            Pairs of (document, histogram) for each known-author document.
        """
        self._known_docs = list(known_docs)

    @abstractmethod
    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Attribute an unknown histogram to one of the known authors.

        Parameters
        ----------
        unknown_histogram:
            The histogram of the unknown document.

        Returns
        -------
        list[Attribution]
            A ranked list of attributions.  Ordering depends on method
            family (see class docstring).
        """


@dataclass
class NeighborAnalysisMethod(AnalysisMethod):
    """Analysis method that relies on a distance function.

    Subclasses use :attr:`distance_function` to compute distances
    between the unknown histogram and each known-author histogram.
    The distance function must be set before calling :meth:`analyze`.
    """

    distance_function: DistanceFunction | None = field(default=None, repr=False)

    def _require_distance_function(self) -> DistanceFunction:
        """Return the distance function, raising if not set."""
        if self.distance_function is None:
            raise PipelineError(
                "distance_function must be set before calling analyze()"
            )
        return self.distance_function


@dataclass
class CentroidAnalysisMethod(NeighborAnalysisMethod):
    """Intermediate base for analysis methods that compare against author centroids.

    Subclasses must populate :attr:`_centroids` in :meth:`train`.
    The shared :meth:`analyze` computes the distance from the unknown
    histogram to each author centroid and ranks by distance ascending.
    """

    _centroids: dict[str, Histogram] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    @staticmethod
    def _accumulate_author_events(
        known_docs: list[tuple[Document, Histogram]],
    ) -> tuple[dict[str, dict[Event, int]], dict[str, int]]:
        """Accumulate per-author event counts and document counts."""
        author_event_sums: dict[str, dict[Event, int]] = defaultdict(dict)
        author_doc_counts: dict[str, int] = defaultdict(int)
        for doc, hist in known_docs:
            author = doc.author or ""
            author_doc_counts[author] += 1
            for event in hist.unique_events():
                count = hist.absolute_frequency(event)
                author_event_sums[author][event] = (
                    author_event_sums[author].get(event, 0) + count
                )
        return author_event_sums, author_doc_counts

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions ranked by distance to each author centroid."""
        df = self._require_distance_function()

        attributions = [
            Attribution(
                author=author,
                score=df.distance(unknown_histogram, centroid),
            )
            for author, centroid in self._centroids.items()
        ]
        attributions.sort(key=lambda a: a.score)
        return attributions


analysis_method_registry: Registry[AnalysisMethod] = Registry[AnalysisMethod](
    "analysis_method"
)

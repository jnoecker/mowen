"""Bagging Nearest Neighbor analysis method."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from mowen.analysis_methods.base import NeighborAnalysisMethod, analysis_method_registry
from mowen.parameters import ParamDef
from mowen.types import Attribution, Document, Event, Histogram


@analysis_method_registry.register("bagging_nn")
@dataclass
class BaggingNearestNeighbor(NeighborAnalysisMethod):
    """Attribute authorship using bootstrap-aggregated nearest neighbor.

    For each author, creates multiple bootstrap samples from the author's
    combined event pool, builds histograms for each sample, and classifies
    the unknown document by finding the nearest sample.  Authors are
    scored by the fraction of their samples that appear in the top
    matches.

    Score semantics: higher = better match (vote-fraction-based).
    """

    lower_is_better: bool = False

    display_name: str = "Bagging Nearest Neighbor"
    description: str = (
        "Bootstrap-aggregated nearest neighbor classification."
    )

    _samples: list[tuple[str, Histogram]] = field(
        default_factory=list, init=False, repr=False,
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="n_samples",
                description="Number of bootstrap samples per author.",
                param_type=int,
                default=5,
                min_value=1,
                max_value=100,
            ),
            ParamDef(
                name="sample_size",
                description="Number of events in each bootstrap sample.",
                param_type=int,
                default=500,
                min_value=10,
                max_value=10000,
            ),
            ParamDef(
                name="random_seed",
                description="Random seed for reproducibility (0 = non-deterministic).",
                param_type=int,
                default=0,
            ),
        ]

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Build bootstrap samples from each author's event pool."""
        super().train(known_docs)

        n_samples: int = self.get_param("n_samples")
        sample_size: int = self.get_param("sample_size")
        seed: int = self.get_param("random_seed")
        rng = random.Random(seed if seed != 0 else None)

        # Aggregate events per author
        author_events: dict[str, list[Event]] = defaultdict(list)
        for doc, hist in self._known_docs:
            author = doc.author or ""
            for event in hist.unique_events():
                count = hist.absolute_frequency(event)
                author_events[author].extend([event] * count)

        # Generate bootstrap samples
        self._samples = []
        for author, events in author_events.items():
            if not events:
                continue
            for _ in range(n_samples):
                sampled = rng.choices(events, k=sample_size)
                counts: dict[Event, int] = {}
                for e in sampled:
                    counts[e] = counts.get(e, 0) + 1
                self._samples.append((author, Histogram(counts)))

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions ranked by fraction of nearest samples."""
        df = self._require_distance_function()

        if not self._samples:
            return []

        n_samples: int = self.get_param("n_samples")

        # Compute distance to every sample
        distances: list[tuple[str, float]] = []
        for author, sample_hist in self._samples:
            dist = df.distance(unknown_histogram, sample_hist)
            distances.append((author, dist))

        # Sort and take top n_samples
        distances.sort(key=lambda x: x[1])
        top = distances[:n_samples]
        actual_n = len(top)

        # Count votes
        votes: Counter[str] = Counter(author for author, _ in top)

        # Include all authors, even those with zero votes
        all_authors = {author for author, _ in self._samples}
        attributions = [
            Attribution(author=author, score=votes.get(author, 0) / actual_n)
            for author in all_authors
        ]
        attributions.sort(key=lambda a: a.score, reverse=True)
        return attributions

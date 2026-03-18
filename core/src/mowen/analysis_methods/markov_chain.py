"""Markov chain (log-likelihood) analysis method."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field

from mowen.analysis_methods.base import AnalysisMethod, analysis_method_registry
from mowen.types import Attribution, Document, Event, Histogram


@analysis_method_registry.register("markov_chain")
@dataclass
class MarkovChain(AnalysisMethod):
    """Attribute authorship using a log-likelihood model.

    For each author, estimate ``P(event | author)`` from the relative
    frequencies of the author's combined training histograms.  For an
    unknown document, compute the log-likelihood under each author's
    distribution:

        LL(author) = sum over events of count(event) * log P(event | author)

    Laplace smoothing (add-one) is applied so unseen events receive a
    small nonzero probability.

    Score semantics: higher = better match (log-likelihood-based).
    """

    lower_is_better: bool = False

    display_name: str = "Markov Chain"
    description: str = (
        "Assigns authorship by computing the log-likelihood of the "
        "unknown document under each author's event distribution."
    )

    _author_distributions: dict[str, dict[Event, float]] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _author_totals: dict[str, int] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _global_vocab: set[Event] = field(
        default_factory=set,
        init=False,
        repr=False,
    )

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Build smoothed probability distributions per author."""
        super().train(known_docs)

        # Aggregate counts per author.
        author_counts: dict[str, dict[Event, int]] = defaultdict(
            lambda: defaultdict(int),
        )
        author_totals: dict[str, int] = defaultdict(int)

        for doc, hist in self._known_docs:
            author = doc.author or ""
            for event in hist.unique_events():
                count = hist.absolute_frequency(event)
                author_counts[author][event] += count
                author_totals[author] += count
            self._global_vocab.update(hist.unique_events())

        # Build smoothed distributions: P(event|author) with Laplace smoothing.
        vocab_size = len(self._global_vocab)
        self._author_distributions = {}
        self._author_vocab_sizes = {}

        for author, counts in author_counts.items():
            total = author_totals[author]
            # Laplace smoothing: (count + 1) / (total + vocab_size)
            denominator = total + vocab_size
            self._author_distributions[author] = {
                event: (counts.get(event, 0) + 1) / denominator
                for event in self._global_vocab
            }
            # Store the per-author smoothing denominator for OOV events
            self._author_totals[author] = total

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions ranked by log-likelihood (highest first)."""
        if not self._author_distributions:
            return []

        vocab_size = len(self._global_vocab)

        attributions: list[Attribution] = []
        for author, dist in self._author_distributions.items():
            log_likelihood = 0.0
            # OOV smoothing: 1 / (author_total + vocab_size), same formula
            # as training but with count=0, so author-specific
            author_total = self._author_totals.get(author, 0)
            oov_prob = 1.0 / (author_total + vocab_size)
            for event in unknown_histogram.unique_events():
                count = unknown_histogram.absolute_frequency(event)
                prob = dist.get(event, oov_prob)
                log_likelihood += count * math.log(prob)
            attributions.append(Attribution(author=author, score=log_likelihood))

        attributions.sort(key=lambda a: a.score, reverse=True)
        return attributions

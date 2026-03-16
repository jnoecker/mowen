"""Naive Bayes analysis method."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mowen.analysis_methods.base import analysis_method_registry
from mowen.analysis_methods.sklearn_base import SklearnAnalysisMethod
from mowen.types import Event, Histogram


@analysis_method_registry.register("naive_bayes")
@dataclass
class NaiveBayes(SklearnAnalysisMethod):
    """Attribute authorship using Multinomial Naive Bayes.

    Training documents are vectorised using absolute frequencies
    (counts) over a shared vocabulary, since ``MultinomialNB`` expects
    non-negative count data.

    Requires ``scikit-learn`` to be installed.

    Score semantics: higher = better match (probability-based).
    """

    display_name: str = "Naive Bayes"
    description: str = (
        "Assigns authorship using Multinomial Naive Bayes "
        "(requires scikit-learn)."
    )

    @staticmethod
    def _vectorize(
        histogram: Histogram, vocabulary: list[Event],
    ) -> list[int]:
        """Convert a histogram into a feature vector of absolute counts."""
        return [histogram.absolute_frequency(event) for event in vocabulary]

    def _create_model(self) -> Any:
        """Return a MultinomialNB estimator."""
        from sklearn.naive_bayes import MultinomialNB  # type: ignore[import-untyped]

        return MultinomialNB()

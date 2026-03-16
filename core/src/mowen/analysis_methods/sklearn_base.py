"""Shared base class for scikit-learn-based analysis methods."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any

from mowen.analysis_methods.base import AnalysisMethod
from mowen.exceptions import PipelineError
from mowen.types import Attribution, Document, Event, Histogram


@dataclass
class SklearnAnalysisMethod(AnalysisMethod):
    """Abstract base for analysis methods backed by a scikit-learn classifier.

    Subclasses only need to implement :meth:`_create_model` to return a
    fitted-ready sklearn estimator.  The shared :meth:`train` builds a
    vocabulary, vectorises the training data, and fits the model.
    :meth:`analyze` calls ``predict_proba`` and returns probability-ranked
    attributions.

    Score semantics: higher = better match (probability-based).
    """

    _vocabulary: list[Event] = field(
        default_factory=list, init=False, repr=False,
    )
    _model: Any = field(default=None, init=False, repr=False)
    _classes: list[str] = field(
        default_factory=list, init=False, repr=False,
    )

    @abstractmethod
    def _create_model(self) -> Any:
        """Return a fresh (unfitted) sklearn estimator."""

    @staticmethod
    def _vectorize(
        histogram: Histogram, vocabulary: list[Event],
    ) -> list[float]:
        """Convert a histogram into a feature vector of relative frequencies."""
        return [histogram.relative_frequency(event) for event in vocabulary]

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Fit the sklearn model on vectorised training histograms."""
        try:
            import sklearn  # noqa: F401  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                f"The {self.display_name} analysis method requires scikit-learn. "
                "Install it with: pip install scikit-learn"
            ) from exc

        super().train(known_docs)

        # Build vocabulary from sorted union of all training events.
        vocab_set: set[Event] = set()
        for _doc, hist in self._known_docs:
            vocab_set.update(hist.unique_events())
        self._vocabulary = sorted(vocab_set, key=lambda e: e.data)

        # Build feature matrix and label vector.
        X: list[list[float | int]] = []
        y: list[str] = []
        for doc, hist in self._known_docs:
            X.append(self._vectorize(hist, self._vocabulary))
            y.append(doc.author or "")

        self._model = self._create_model()
        self._model.fit(X, y)
        self._classes = list(self._model.classes_)

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions ranked by predicted class probability."""
        if self._model is None:
            raise PipelineError("train() must be called before analyze()")

        try:
            import sklearn  # noqa: F401  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                f"The {self.display_name} analysis method requires scikit-learn. "
                "Install it with: pip install scikit-learn"
            ) from exc

        vector = [self._vectorize(unknown_histogram, self._vocabulary)]
        probabilities = self._model.predict_proba(vector)[0]

        attributions = [
            Attribution(author=author, score=float(prob))
            for author, prob in zip(self._classes, probabilities)
        ]
        attributions.sort(key=lambda a: a.score, reverse=True)
        return attributions

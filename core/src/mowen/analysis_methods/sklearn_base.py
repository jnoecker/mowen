"""Shared base class for scikit-learn-based analysis methods."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any

from mowen.analysis_methods.base import AnalysisMethod
from mowen.exceptions import PipelineError
from mowen.types import Attribution, Document, Event, Histogram, NumericEventSet


@dataclass
class SklearnAnalysisMethod(AnalysisMethod):
    """Abstract base for analysis methods backed by a scikit-learn classifier.

    Subclasses only need to implement :meth:`_create_model` to return a
    fitted-ready sklearn estimator.  The shared :meth:`train` builds a
    vocabulary, vectorises the training data, and fits the model.
    :meth:`analyze` calls ``predict_proba`` and returns probability-ranked
    attributions.

    When the pipeline passes :class:`~mowen.types.NumericEventSet` objects
    (e.g. from transformer embeddings), the vectorisation step is skipped
    and the raw float vectors are used directly as feature inputs.

    Score semantics: higher = better match (probability-based).
    """

    lower_is_better: bool = False

    _vocabulary: list[Event] = field(
        default_factory=list,
        init=False,
        repr=False,
    )
    _model: Any = field(default=None, init=False, repr=False)
    _classes: list[str] = field(
        default_factory=list,
        init=False,
        repr=False,
    )
    _numeric_mode: bool = field(default=False, init=False, repr=False)

    @abstractmethod
    def _create_model(self) -> Any:
        """Return a fresh (unfitted) sklearn estimator."""

    @staticmethod
    def _vectorize(
        histogram: Histogram,
        vocabulary: list[Event],
    ) -> list[float]:
        """Convert a histogram into a feature vector of relative frequencies."""
        return [histogram.relative_frequency(event) for event in vocabulary]

    def _ensure_sklearn(self) -> None:
        try:
            import sklearn  # noqa: F401  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                f"The {self.display_name} analysis method requires scikit-learn. "
                "Install it with: pip install scikit-learn"
            ) from exc

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Fit the sklearn model on training data.

        Accepts either Histogram objects (vectorised via vocabulary) or
        NumericEventSet objects (used directly as feature vectors).
        """
        self._ensure_sklearn()
        super().train(known_docs)

        # Detect whether we're in numeric (embedding) mode
        self._numeric_mode = any(
            isinstance(hist, NumericEventSet) for _, hist in self._known_docs
        )

        X: list[list[float]] = []
        y: list[str] = []

        if self._numeric_mode:
            for doc, hist in self._known_docs:
                X.append(list(hist))  # NumericEventSet is list[float]
                y.append(doc.author or "")
        else:
            # Build vocabulary from sorted union of all training events
            vocab_set: set[Event] = set()
            for _doc, hist in self._known_docs:
                vocab_set.update(hist.unique_events())
            self._vocabulary = sorted(vocab_set, key=lambda e: e.data)

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
        self._ensure_sklearn()

        if self._numeric_mode:
            vector = [list(unknown_histogram)]  # NumericEventSet is list[float]
        else:
            vector = [self._vectorize(unknown_histogram, self._vocabulary)]

        probabilities = self._model.predict_proba(vector)[0]

        attributions = [
            Attribution(author=author, score=float(prob))
            for author, prob in zip(self._classes, probabilities)
        ]
        attributions.sort(key=lambda a: a.score, reverse=True)
        return attributions

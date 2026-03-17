"""Unmasking analysis method (Koppel & Schler 2004).

Authorship verification method that iteratively trains SVMs and removes
the most discriminative features.  If accuracy drops quickly, the texts
are likely by the same author (surface differences are shallow).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from mowen.analysis_methods.base import AnalysisMethod, analysis_method_registry
from mowen.parameters import ParamDef
from mowen.types import Attribution, Document, Event, Histogram


@analysis_method_registry.register("unmasking")
@dataclass
class Unmasking(AnalysisMethod):
    """Attribute authorship using the Unmasking technique.

    For each candidate author, labels that author's documents as "same"
    and all others as "different", then iteratively trains linear SVMs
    and removes the features with the highest absolute coefficients.
    A fast accuracy drop indicates same-author texts.

    Score = initial_accuracy - final_accuracy (higher = more likely same author).

    Score semantics: higher = more likely same author.
    """

    lower_is_better: bool = False
    verification_threshold: float = 0.5

    display_name: str = "Unmasking"
    description: str = (
        "Iterative SVM feature elimination for authorship verification "
        "(Koppel & Schler 2004)."
    )

    _author_histograms: dict[str, list[Histogram]] = field(
        default_factory=dict, init=False, repr=False,
    )
    _all_events: list[Event] = field(
        default_factory=list, init=False, repr=False,
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="n_features",
                description="Number of top-frequency features to use initially.",
                param_type=int,
                default=250,
                min_value=2,
                max_value=10000,
            ),
            ParamDef(
                name="n_eliminate",
                description="Number of features to eliminate per iteration.",
                param_type=int,
                default=6,
                min_value=1,
                max_value=100,
            ),
            ParamDef(
                name="n_iterations",
                description="Number of unmasking iterations.",
                param_type=int,
                default=10,
                min_value=2,
                max_value=100,
            ),
            ParamDef(
                name="n_folds",
                description="Number of cross-validation folds for SVM accuracy.",
                param_type=int,
                default=10,
                min_value=2,
                max_value=50,
            ),
            ParamDef(
                name="random_seed",
                description="Random seed for reproducibility (0 = non-deterministic).",
                param_type=int,
                default=0,
            ),
        ]

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Group known documents by author and find top events by frequency."""
        super().train(known_docs)

        self._author_histograms = defaultdict(list)
        event_totals: dict[Event, int] = defaultdict(int)

        for doc, hist in self._known_docs:
            author = doc.author or ""
            self._author_histograms[author].append(hist)
            for event in hist.unique_events():
                event_totals[event] += hist.absolute_frequency(event)

        # Select top-N most frequent events across the corpus
        n_features: int = self.get_param("n_features")
        sorted_events = sorted(event_totals.items(), key=lambda x: x[1], reverse=True)
        self._all_events = [e for e, _ in sorted_events[:n_features]]

    def _histogram_to_vector(self, hist: Histogram, events: list[Event]) -> list[float]:
        """Convert a histogram to a feature vector using relative frequencies."""
        total = hist.total
        if total == 0:
            return [0.0] * len(events)
        return [hist.absolute_frequency(e) / total for e in events]

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions ranked by unmasking accuracy drop."""
        try:
            from sklearn.model_selection import cross_val_score
            from sklearn.svm import LinearSVC
        except ImportError:
            raise ImportError(
                "Unmasking requires scikit-learn. Install it with: "
                "pip install scikit-learn"
            )

        import numpy as np

        n_eliminate: int = self.get_param("n_eliminate")
        n_iterations: int = self.get_param("n_iterations")
        n_folds: int = self.get_param("n_folds")
        seed: int = self.get_param("random_seed")
        rng_seed = seed if seed != 0 else None

        authors = list(self._author_histograms.keys())
        attributions: list[Attribution] = []

        for candidate in authors:
            # Build labeled dataset: candidate = 1, others = 0
            vectors: list[list[float]] = []
            labels: list[int] = []

            for author, hists in self._author_histograms.items():
                label = 1 if author == candidate else 0
                for hist in hists:
                    vectors.append(self._histogram_to_vector(hist, self._all_events))
                    labels.append(label)

            # Add the unknown document as positive (same-author hypothesis)
            vectors.append(self._histogram_to_vector(unknown_histogram, self._all_events))
            labels.append(1)

            x_data = np.array(vectors)
            y_data = np.array(labels)

            # Need at least n_folds samples of each class for cross-validation
            n_positive = int(np.sum(y_data == 1))
            n_negative = int(np.sum(y_data == 0))
            actual_folds = min(n_folds, n_positive, n_negative)

            if actual_folds < 2:
                # Not enough data for cross-validation; assign neutral score
                attributions.append(Attribution(author=candidate, score=0.0))
                continue

            # Track which features are still active
            active_features = list(range(len(self._all_events)))
            accuracies: list[float] = []

            for iteration in range(n_iterations):
                if len(active_features) < n_eliminate + 1:
                    break

                x_active = x_data[:, active_features]

                svm = LinearSVC(random_state=rng_seed, max_iter=10000, dual="auto")
                try:
                    scores = cross_val_score(svm, x_active, y_data, cv=actual_folds)
                    acc = float(np.mean(scores))
                except Exception:
                    # SVM may fail if features are degenerate
                    acc = 0.5
                accuracies.append(acc)

                # Train on full data to get coefficients for elimination
                svm.fit(x_active, y_data)
                coefs = np.abs(svm.coef_[0])

                # Remove features with highest absolute coefficients
                top_indices = np.argsort(coefs)[-n_eliminate:]
                remove_set = set(top_indices.tolist())
                active_features = [
                    f for i, f in enumerate(active_features) if i not in remove_set
                ]

            if len(accuracies) >= 2:
                score = accuracies[0] - accuracies[-1]
            else:
                score = 0.0

            attributions.append(Attribution(author=candidate, score=score))

        attributions.sort(key=lambda a: a.score, reverse=True)
        return attributions

"""Linear Discriminant Analysis method."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mowen.analysis_methods.base import analysis_method_registry
from mowen.analysis_methods.sklearn_base import SklearnAnalysisMethod


@analysis_method_registry.register("lda")
@dataclass
class LDA(SklearnAnalysisMethod):
    """Attribute authorship using Linear Discriminant Analysis.

    Training documents are vectorised using relative frequencies over a
    shared vocabulary.  ``sklearn.discriminant_analysis.LinearDiscriminantAnalysis``
    is fitted and ``predict_proba`` is used to rank authors.

    Requires ``scikit-learn`` to be installed.

    Score semantics: higher = better match (probability-based).
    """

    display_name: str = "Linear Discriminant Analysis"
    description: str = (
        "Assigns authorship using Linear Discriminant Analysis "
        "(requires scikit-learn)."
    )

    def _create_model(self) -> Any:
        """Return a LinearDiscriminantAnalysis estimator."""
        from sklearn.discriminant_analysis import (  # type: ignore[import-untyped]
            LinearDiscriminantAnalysis,
        )

        return LinearDiscriminantAnalysis()

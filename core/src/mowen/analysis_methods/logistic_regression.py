"""Logistic Regression analysis method."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mowen.analysis_methods.base import analysis_method_registry
from mowen.analysis_methods.sklearn_base import SklearnAnalysisMethod


@analysis_method_registry.register("logistic_regression")
@dataclass
class LogisticRegression(SklearnAnalysisMethod):
    """Attribute authorship using Logistic Regression.

    A standard linear classifier with probabilistic output.  Often
    a strong baseline for authorship attribution.

    Requires ``scikit-learn`` to be installed.

    Score semantics: higher = better match (probability-based).
    """

    display_name: str = "Logistic Regression"
    description: str = (
        "Assigns authorship using Logistic Regression " "(requires scikit-learn)."
    )

    def _create_model(self) -> Any:
        from sklearn.linear_model import LogisticRegression as LR  # type: ignore[import-untyped]

        return LR(max_iter=1000)

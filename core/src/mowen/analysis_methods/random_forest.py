"""Random Forest analysis method."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mowen.analysis_methods.base import analysis_method_registry
from mowen.analysis_methods.sklearn_base import SklearnAnalysisMethod
from mowen.parameters import ParamDef


@analysis_method_registry.register("random_forest")
@dataclass
class RandomForest(SklearnAnalysisMethod):
    """Attribute authorship using a Random Forest ensemble classifier.

    An ensemble of decision trees trained on random subsets of features.
    Generally more robust than a single decision tree.

    Requires ``scikit-learn`` to be installed.

    Score semantics: higher = better match (probability-based).
    """

    display_name: str = "Random Forest"
    description: str = (
        "Assigns authorship using a Random Forest classifier "
        "(requires scikit-learn)."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="n_estimators",
                description="Number of trees in the forest.",
                param_type=int,
                default=100,
                min_value=1,
                max_value=1000,
            ),
            ParamDef(
                name="max_depth",
                description="Maximum depth of each tree (0 = unlimited).",
                param_type=int,
                default=0,
                min_value=0,
                max_value=100,
            ),
        ]

    def _create_model(self) -> Any:
        from sklearn.ensemble import RandomForestClassifier  # type: ignore[import-untyped]

        n_estimators: int = self.get_param("n_estimators")
        max_depth: int = self.get_param("max_depth")
        return RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth if max_depth > 0 else None,
        )

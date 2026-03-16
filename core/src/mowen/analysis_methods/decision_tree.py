"""Decision tree analysis method."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mowen.analysis_methods.base import analysis_method_registry
from mowen.analysis_methods.sklearn_base import SklearnAnalysisMethod
from mowen.parameters import ParamDef


@analysis_method_registry.register("decision_tree")
@dataclass
class DecisionTree(SklearnAnalysisMethod):
    """Attribute authorship using a Decision Tree classifier.

    Training documents are vectorised using relative frequencies over a
    shared vocabulary.  An ``sklearn.tree.DecisionTreeClassifier`` is
    fitted and ``predict_proba`` is used to rank authors.

    Requires ``scikit-learn`` to be installed.

    Score semantics: higher = better match (probability-based).
    """

    display_name: str = "Decision Tree"
    description: str = (
        "Assigns authorship using a Decision Tree classifier "
        "(requires scikit-learn)."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        """Declare the max_depth parameter."""
        return [
            ParamDef(
                name="max_depth",
                description="Maximum depth of the decision tree.",
                param_type=int,
                default=10,
                min_value=1,
                max_value=100,
            ),
        ]

    def _create_model(self) -> Any:
        """Return a DecisionTreeClassifier with the configured max_depth."""
        from sklearn.tree import DecisionTreeClassifier  # type: ignore[import-untyped]

        max_depth: int = self.get_param("max_depth")
        return DecisionTreeClassifier(max_depth=max_depth)

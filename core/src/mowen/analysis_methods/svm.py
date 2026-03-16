"""SVM (Support Vector Machine) analysis method."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mowen.analysis_methods.base import analysis_method_registry
from mowen.analysis_methods.sklearn_base import SklearnAnalysisMethod
from mowen.parameters import ParamDef


@analysis_method_registry.register("svm")
@dataclass
class SVM(SklearnAnalysisMethod):
    """Attribute authorship using a Support Vector Machine classifier.

    Training documents are vectorised using relative frequencies over a
    shared vocabulary.  An ``sklearn.svm.SVC`` is fitted with
    ``probability=True`` to enable probabilistic predictions.

    Requires ``scikit-learn`` to be installed.

    Score semantics: higher = better match (probability-based).
    """

    display_name: str = "SVM"
    description: str = (
        "Assigns authorship using a Support Vector Machine classifier "
        "(requires scikit-learn)."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        """Declare the kernel parameter."""
        return [
            ParamDef(
                name="kernel",
                description="SVM kernel type.",
                param_type=str,
                default="linear",
                choices=["linear", "rbf", "poly"],
            ),
        ]

    def _create_model(self) -> Any:
        """Return an SVC configured with the chosen kernel."""
        from sklearn.svm import SVC  # type: ignore[import-untyped]

        kernel: str = self.get_param("kernel")
        return SVC(kernel=kernel, probability=True)

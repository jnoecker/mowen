"""Multilayer Perceptron (neural network) analysis method."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mowen.analysis_methods.base import analysis_method_registry
from mowen.analysis_methods.sklearn_base import SklearnAnalysisMethod
from mowen.parameters import ParamDef


@analysis_method_registry.register("mlp")
@dataclass
class MultilayerPerceptron(SklearnAnalysisMethod):
    """Attribute authorship using a Multilayer Perceptron neural network.

    A feedforward neural network with configurable hidden layer size.
    Capable of learning non-linear decision boundaries.

    Requires ``scikit-learn`` to be installed.

    Score semantics: higher = better match (probability-based).
    """

    display_name: str = "Multilayer Perceptron"
    description: str = (
        "Assigns authorship using a neural network "
        "(requires scikit-learn)."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="hidden_size",
                description="Number of neurons in the hidden layer.",
                param_type=int,
                default=100,
                min_value=1,
                max_value=1000,
            ),
            ParamDef(
                name="max_iter",
                description="Maximum training iterations.",
                param_type=int,
                default=500,
                min_value=10,
                max_value=5000,
            ),
        ]

    def _create_model(self) -> Any:
        from sklearn.neural_network import MLPClassifier  # type: ignore[import-untyped]

        hidden_size: int = self.get_param("hidden_size")
        max_iter: int = self.get_param("max_iter")
        return MLPClassifier(
            hidden_layer_sizes=(hidden_size,),
            max_iter=max_iter,
        )

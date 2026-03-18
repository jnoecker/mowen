"""Multilayer Perceptron (neural network) analysis method.

Supports optional R-Drop regularization (torch-based) for improved
robustness.  When ``r_drop=False`` (default), uses scikit-learn's
MLPClassifier.  When ``r_drop=True``, trains a simple torch MLP with
R-Drop (Regularized Dropout) loss.

GPU acceleration is available when ``r_drop=True``.  Set the ``device``
parameter to ``"auto"`` (default) to auto-detect CUDA or MPS, or
specify ``"cpu"``, ``"cuda"``, or ``"mps"`` explicitly.

Reference for R-Drop: Liang et al. (NeurIPS 2021).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mowen.analysis_methods.base import analysis_method_registry
from mowen.analysis_methods.sklearn_base import SklearnAnalysisMethod
from mowen.exceptions import PipelineError
from mowen.parameters import ParamDef
from mowen.types import Attribution, Document, Event, Histogram, NumericEventSet


@analysis_method_registry.register("mlp")
@dataclass
class MultilayerPerceptron(SklearnAnalysisMethod):
    """Attribute authorship using a Multilayer Perceptron neural network.

    A feedforward neural network with configurable hidden layer size.
    Capable of learning non-linear decision boundaries.

    With ``r_drop=True``, uses a torch-based MLP trained with R-Drop
    regularization (requires torch).  Otherwise uses scikit-learn.

    Score semantics: higher = better match (probability-based).
    """

    display_name: str = "Multilayer Perceptron"
    description: str = (
        "Assigns authorship using a neural network "
        "(requires scikit-learn; optionally torch for R-Drop)."
    )

    _torch_model: Any = field(default=None, init=False, repr=False)
    _torch_classes: list[str] = field(
        default_factory=list, init=False, repr=False,
    )
    _rdrop_active: bool = field(default=False, init=False, repr=False)
    _device: Any = field(default=None, init=False, repr=False)

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
            ParamDef(
                name="r_drop",
                description=(
                    "Enable R-Drop regularization (requires torch). "
                    "When disabled, uses scikit-learn MLPClassifier."
                ),
                param_type=bool,
                default=False,
            ),
            ParamDef(
                name="r_drop_alpha",
                description="Weight of R-Drop KL divergence loss.",
                param_type=float,
                default=1.0,
                min_value=0.0,
                max_value=100.0,
            ),
            ParamDef(
                name="dropout",
                description="Dropout rate for R-Drop MLP.",
                param_type=float,
                default=0.3,
                min_value=0.0,
                max_value=0.9,
            ),
            ParamDef(
                name="learning_rate",
                description="Learning rate for R-Drop optimizer.",
                param_type=float,
                default=0.001,
                min_value=1e-6,
                max_value=1.0,
            ),
            ParamDef(
                name="device",
                description=(
                    "Device for R-Drop training: auto (detect GPU), "
                    "cpu, cuda, or mps."
                ),
                param_type=str,
                default="auto",
                choices=["auto", "cpu", "cuda", "mps"],
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

    @staticmethod
    def _resolve_device(device_param: str) -> Any:
        """Return a ``torch.device`` from the user-facing parameter.

        When *device_param* is ``"auto"``, selects CUDA if available,
        then MPS (Apple Silicon), otherwise CPU.
        """
        import torch

        if device_param == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return torch.device("mps")
            return torch.device("cpu")
        return torch.device(device_param)

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Train with sklearn or R-Drop torch path."""
        r_drop: bool = self.get_param("r_drop")

        if not r_drop:
            # Standard sklearn path
            self._rdrop_active = False
            super().train(known_docs)
            return

        # R-Drop torch path
        self._rdrop_active = True
        self._known_docs = list(known_docs)

        try:
            import torch
            import torch.nn as nn
        except ImportError as exc:
            raise ImportError(
                "R-Drop regularization requires PyTorch. "
                "Install with: pip install torch"
            ) from exc

        device = self._resolve_device(self.get_param("device"))
        self._device = device

        # Detect numeric mode and build feature matrix
        self._numeric_mode = any(
            isinstance(hist, NumericEventSet)
            for _, hist in self._known_docs
        )

        x_list: list[list[float]] = []
        y_list: list[str] = []

        if self._numeric_mode:
            for doc, hist in self._known_docs:
                x_list.append(list(hist))
                y_list.append(doc.author or "")
        else:
            vocab_set: set[Event] = set()
            for _, hist in self._known_docs:
                vocab_set.update(hist.unique_events())
            self._vocabulary = sorted(vocab_set, key=lambda e: e.data)
            for doc, hist in self._known_docs:
                x_list.append(self._vectorize(hist, self._vocabulary))
                y_list.append(doc.author or "")

        # Encode labels
        unique_authors = sorted(set(y_list))
        self._torch_classes = unique_authors
        label_map = {a: i for i, a in enumerate(unique_authors)}
        y_encoded = [label_map[a] for a in y_list]

        input_dim = len(x_list[0])
        n_classes = len(unique_authors)
        hidden_size: int = self.get_param("hidden_size")
        dropout: float = self.get_param("dropout")
        alpha: float = self.get_param("r_drop_alpha")
        lr: float = self.get_param("learning_rate")
        max_iter: int = self.get_param("max_iter")

        # Build torch model and move to device
        model = nn.Sequential(
            nn.Linear(input_dim, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, n_classes),
        ).to(device)

        x_tensor = torch.tensor(x_list, dtype=torch.float32, device=device)
        y_tensor = torch.tensor(y_encoded, dtype=torch.long, device=device)

        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        ce_loss = nn.CrossEntropyLoss()

        for _ in range(max_iter):
            model.train()

            # Double forward pass (different dropout masks)
            logits1 = model(x_tensor)
            logits2 = model(x_tensor)

            loss1 = ce_loss(logits1, y_tensor)
            loss2 = ce_loss(logits2, y_tensor)

            # KL divergence between the two distributions
            p1 = torch.nn.functional.softmax(logits1, dim=-1)
            p2 = torch.nn.functional.softmax(logits2, dim=-1)
            kl_1 = torch.nn.functional.kl_div(
                p1.log(), p2, reduction="batchmean",
            )
            kl_2 = torch.nn.functional.kl_div(
                p2.log(), p1, reduction="batchmean",
            )
            kl_loss = (kl_1 + kl_2) / 2

            total_loss = (loss1 + loss2) / 2 + alpha * kl_loss

            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()

        model.eval()
        self._torch_model = model

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions from sklearn or torch model."""
        if not self._rdrop_active:
            return super().analyze(unknown_histogram)

        import torch

        if self._torch_model is None:
            raise PipelineError(
                "train() must be called before analyze()"
            )

        if self._numeric_mode:
            vec = list(unknown_histogram)
        else:
            vec = self._vectorize(unknown_histogram, self._vocabulary)

        device = self._device or torch.device("cpu")
        x = torch.tensor([vec], dtype=torch.float32, device=device)
        with torch.no_grad():
            logits = self._torch_model(x)
            probs = torch.nn.functional.softmax(logits, dim=-1)[0]

        attributions = [
            Attribution(author=author, score=float(probs[i]))
            for i, author in enumerate(self._torch_classes)
        ]
        attributions.sort(key=lambda a: a.score, reverse=True)
        return attributions

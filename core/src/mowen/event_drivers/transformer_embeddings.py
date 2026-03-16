"""Transformer embedding event driver using HuggingFace models."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.types import EventSet, NumericEventSet


@event_driver_registry.register("transformer_embeddings")
@dataclass
class TransformerEmbeddingDriver(EventDriver):
    """Produce dense embedding vectors from a pre-trained transformer model.

    Returns a :class:`~mowen.types.NumericEventSet` (a dense float vector)
    instead of a discrete :class:`~mowen.types.EventSet`.  Analysis methods
    backed by scikit-learn classifiers accept these directly as feature vectors,
    bypassing the histogram and distance-function stages.
    """

    display_name: str = "Transformer Embeddings"
    description: str = (
        "Dense vector embeddings from a HuggingFace transformer model. "
        "Compatible with sklearn-based analysis methods (SVM, LDA, etc.)."
    )

    _tokenizer: object = None
    _model: object = None
    _model_name_cache: str = ""

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="model_name",
                description="HuggingFace model name or path",
                param_type=str,
                default="sentence-transformers/all-MiniLM-L6-v2",
            ),
            ParamDef(
                name="max_length",
                description="Maximum token length for truncation",
                param_type=int,
                default=512,
                min_value=16,
                max_value=8192,
            ),
        ]

    def _ensure_model(self) -> None:
        """Lazy-load the transformer model on first use."""
        model_name = self.get_param("model_name")
        if self._model is not None and self._model_name_cache == model_name:
            return

        try:
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "Transformer embeddings require the transformers library. "
                "Install with: pip install 'mowen[transformers]'"
            ) from exc

        try:
            import torch  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "Transformer embeddings require PyTorch. "
                "Install with: pip install torch"
            ) from exc

        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModel.from_pretrained(model_name)
        self._model.eval()
        self._model_name_cache = model_name

    def create_event_set(self, text: str) -> EventSet:
        """Return a NumericEventSet containing the mean-pooled embedding.

        The return type is declared as EventSet for interface compatibility,
        but the actual object is a NumericEventSet (list[float]).
        """
        import torch

        self._ensure_model()
        max_length = self.get_param("max_length")

        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
            padding=True,
        )

        with torch.no_grad():
            outputs = self._model(**inputs)

        # Mean pooling over token dimension, respecting attention mask
        attention_mask = inputs["attention_mask"]
        token_embeddings = outputs.last_hidden_state
        mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = (token_embeddings * mask_expanded).sum(dim=1)
        sum_mask = mask_expanded.sum(dim=1).clamp(min=1e-9)
        embedding = (sum_embeddings / sum_mask).squeeze(0)

        return NumericEventSet(embedding.tolist())  # type: ignore[return-value]

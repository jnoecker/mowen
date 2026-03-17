"""SELMA: Style Embeddings from Language Models for Authorship.

Instruction-tuned embedding driver that uses models like
e5-mistral-7b-instruct to produce stylistically-aware document
embeddings.  The instruction prefix steers the model toward
capturing stylistic features rather than topical content.

Reference: Ma et al. (AAAI 2025), Wang et al. (2024).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.types import NumericEventSet


@event_driver_registry.register("selma_embeddings")
@dataclass
class SELMAEmbeddingDriver(EventDriver):
    """Produce style-aware embeddings using an instruction-tuned model.

    Prepends a stylistic retrieval instruction to the text, then extracts
    the last-token (EOS) embedding from the final transformer layer.
    Returns a :class:`~mowen.types.NumericEventSet`.

    Requires ``transformers`` and ``torch``.  Install with::

        pip install 'mowen[transformers]'
    """

    display_name: str = "SELMA Instruction-Tuned Embeddings"
    description: str = (
        "Instruction-tuned transformer embeddings optimized for "
        "stylistic similarity (requires transformers extra)."
    )

    _tokenizer: object = field(default=None, init=False, repr=False)
    _model: object = field(default=None, init=False, repr=False)
    _model_name_cache: str = field(default="", init=False, repr=False)

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="model_name",
                description=(
                    "HuggingFace instruction-tuned embedding model."
                ),
                param_type=str,
                default="intfloat/e5-mistral-7b-instruct",
            ),
            ParamDef(
                name="max_length",
                description="Maximum token length for truncation.",
                param_type=int,
                default=4096,
                min_value=16,
                max_value=32768,
            ),
            ParamDef(
                name="instruction",
                description="Instruction prefix for stylistic embedding.",
                param_type=str,
                default="Retrieve stylistically similar text",
            ),
        ]

    def _ensure_model(self) -> None:
        """Lazy-load the model on first use."""
        model_name = self.get_param("model_name")
        if self._model is not None and self._model_name_cache == model_name:
            return

        try:
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "SELMA embeddings require the transformers library. "
                "Install with: pip install 'mowen[transformers]'"
            ) from exc

        try:
            import torch  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "SELMA embeddings require PyTorch. "
                "Install with: pip install torch"
            ) from exc

        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModel.from_pretrained(model_name)
        self._model.eval()
        self._model_name_cache = model_name

    def create_event_set(self, text: str) -> NumericEventSet:
        """Return a NumericEventSet from instruction-tuned embedding."""
        import torch

        self._ensure_model()
        max_length = self.get_param("max_length")
        instruction = self.get_param("instruction")

        # Prepend instruction prefix (e5-instruct convention)
        query = f"Instruct: {instruction}\nQuery: {text}"

        inputs = self._tokenizer(
            query,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
            padding=True,
        )

        with torch.no_grad():
            outputs = self._model(**inputs)

        # Extract last-token embedding (EOS position)
        # For instruction-tuned models, the last token captures
        # the full sequence representation.
        last_hidden = outputs.last_hidden_state
        # Find the position of the last real token (before padding)
        seq_lengths = inputs["attention_mask"].sum(dim=1) - 1
        embedding = last_hidden[0, seq_lengths[0].item(), :]

        # L2 normalize
        embedding = torch.nn.functional.normalize(embedding, dim=0)

        return NumericEventSet(embedding.tolist())

"""Perplexity / surprisal feature extraction from causal language models.

Computes per-token negative log-likelihood (surprisal) statistics using a
causal LM (GPT-2 by default).  The summary statistics (mean, variance,
skewness, kurtosis) capture a document's predictability profile, which
varies by author.

Reference: Basani & Chen (PAN 2025), Sun et al. (PAN 2025).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.types import NumericEventSet


def _statistics(values: list[float]) -> tuple[float, float, float, float]:
    """Compute mean, variance, skewness, kurtosis (pure Python)."""
    n = len(values)
    if n == 0:
        return (0.0, 0.0, 0.0, 0.0)

    mean = sum(values) / n
    if n < 2:
        return (mean, 0.0, 0.0, 0.0)

    var = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(var) if var > 0 else 1e-12

    skew = sum(((x - mean) / std) ** 3 for x in values) / n
    kurt = sum(((x - mean) / std) ** 4 for x in values) / n - 3.0

    return (mean, var, skew, kurt)


@event_driver_registry.register("perplexity")
@dataclass
class PerplexityDriver(EventDriver):
    """Extract surprisal statistics from a causal language model.

    Returns a :class:`~mowen.types.NumericEventSet` with 4 features:
    mean, variance, skewness, and kurtosis of per-token surprisal
    (negative log-likelihood).

    Requires ``transformers`` and ``torch``.  Install with::

        pip install 'mowen[transformers]'
    """

    display_name: str = "Perplexity / Surprisal Features"
    description: str = (
        "Statistical features of per-token surprisal from a causal "
        "language model (requires transformers extra)."
    )

    _tokenizer: object = field(default=None, init=False, repr=False)
    _model: object = field(default=None, init=False, repr=False)
    _model_name_cache: str = field(default="", init=False, repr=False)

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="model_name",
                description="HuggingFace causal language model.",
                param_type=str,
                default="gpt2",
            ),
            ParamDef(
                name="max_length",
                description="Maximum token length per chunk.",
                param_type=int,
                default=1024,
                min_value=16,
                max_value=4096,
            ),
        ]

    def _ensure_model(self) -> None:
        """Lazy-load the causal LM on first use."""
        model_name = self.get_param("model_name")
        if self._model is not None and self._model_name_cache == model_name:
            return

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "Perplexity features require the transformers library. "
                "Install with: pip install 'mowen[transformers]'"
            ) from exc

        try:
            import torch  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "Perplexity features require PyTorch. "
                "Install with: pip install torch"
            ) from exc

        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForCausalLM.from_pretrained(model_name)
        self._model.eval()
        self._model_name_cache = model_name

    def create_event_set(self, text: str) -> NumericEventSet:
        """Return a NumericEventSet of surprisal statistics."""
        import torch

        self._ensure_model()
        max_length = self.get_param("max_length")

        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
        )

        input_ids = inputs["input_ids"]

        with torch.no_grad():
            outputs = self._model(**inputs)
            logits = outputs.logits  # (1, seq_len, vocab_size)

        # Compute per-token surprisal (shifted by 1 for causal LM)
        # logits[0, t, :] predicts token at position t+1
        surprisals: list[float] = []
        log_probs = torch.nn.functional.log_softmax(logits[0], dim=-1)

        for t in range(input_ids.size(1) - 1):
            next_token = input_ids[0, t + 1].item()
            token_log_prob = log_probs[t, next_token].item()
            surprisals.append(-token_log_prob)

        if not surprisals:
            return NumericEventSet([float("nan")] * 4)

        mean, var, skew, kurt = _statistics(surprisals)
        return NumericEventSet([mean, var, skew, kurt])

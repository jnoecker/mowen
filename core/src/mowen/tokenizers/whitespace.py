"""Whitespace tokenizer — the default word segmentation strategy."""

from __future__ import annotations

from mowen.tokenizers.base import Tokenizer, tokenizer_registry


@tokenizer_registry.register("whitespace")
class WhitespaceTokenizer(Tokenizer):
    """Split text on whitespace into word tokens.

    This is the default tokenizer and produces the same result as
    ``str.split()``.
    """

    display_name = "Whitespace"
    description = "Split on whitespace (default for space-delimited languages)."

    def tokenize(self, text: str) -> list[str]:
        return text.split()

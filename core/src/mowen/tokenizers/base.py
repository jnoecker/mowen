"""Base tokenizer class and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from mowen.parameters import Configurable, ParamDef
from mowen.registry import Registry


@dataclass
class Tokenizer(ABC, Configurable):
    """Abstract base class for word tokenizers.

    A tokenizer splits text into a list of word tokens.  The default
    implementation splits on whitespace; language-specific tokenizers
    (e.g. Chinese segmentation via jieba) can be registered and
    selected via the ``tokenizer`` parameter on word-based event drivers.
    """

    display_name: str = ""
    description: str = ""

    @abstractmethod
    def tokenize(self, text: str) -> list[str]:
        """Split *text* into word tokens."""


tokenizer_registry: Registry[Tokenizer] = Registry[Tokenizer]("tokenizer")


def _get_tokenizer(name: str) -> Tokenizer:
    """Look up and instantiate a tokenizer by registry name."""
    return tokenizer_registry.create(name)


# Shared ParamDef that word-based event drivers include in their param_defs().
TOKENIZER_PARAM = ParamDef(
    name="tokenizer",
    description="Tokenizer for word segmentation (e.g. 'whitespace', 'jieba').",
    param_type=str,
    default="whitespace",
)


def tokenize_text(text: str, tokenizer_name: str = "whitespace") -> list[str]:
    """Convenience function: tokenize text using a named tokenizer."""
    tok = tokenizer_registry.create(tokenizer_name)
    return tok.tokenize(text)

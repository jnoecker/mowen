"""Canonicizer that adds spaces around punctuation characters."""

from __future__ import annotations

import re
import string
from dataclasses import dataclass

from mowen.canonicizers.base import Canonicizer, canonicizer_registry

# Build a pattern that matches any single punctuation character.
_PUNCTUATION_PATTERN = re.compile("([" + re.escape(string.punctuation) + "])")


@canonicizer_registry.register("punctuation_separator")
@dataclass
class PunctuationSeparator(Canonicizer):
    """Add spaces around punctuation so they become separate tokens."""

    display_name: str = "Punctuation Separator"
    description: str = (
        "Adds spaces around punctuation characters so they become " "separate tokens."
    )

    def process(self, text: str) -> str:
        """Return *text* with spaces inserted around every punctuation character."""
        return _PUNCTUATION_PATTERN.sub(r" \1 ", text)

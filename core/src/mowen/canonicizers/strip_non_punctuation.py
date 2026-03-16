"""Canonicizer that removes everything except punctuation and whitespace."""

from __future__ import annotations

import re
import string
from dataclasses import dataclass

from mowen.canonicizers.base import Canonicizer, canonicizer_registry

# Match any character that is NOT punctuation and NOT whitespace.
_NON_PUNCT_PATTERN = re.compile(
    "[^" + re.escape(string.punctuation) + r"\s]"
)


@canonicizer_registry.register("strip_non_punctuation")
@dataclass
class StripNonPunctuation(Canonicizer):
    """Remove everything that is not punctuation, keeping punctuation and whitespace."""

    display_name: str = "Strip Non-Punctuation"
    description: str = (
        "Removes all characters that are not punctuation, "
        "keeping only punctuation characters and whitespace."
    )

    def process(self, text: str) -> str:
        """Return *text* with only punctuation and whitespace retained."""
        return _NON_PUNCT_PATTERN.sub("", text)

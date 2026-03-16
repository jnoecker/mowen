"""Canonicizer that removes punctuation characters."""

from __future__ import annotations

import string
from dataclasses import dataclass

from mowen.canonicizers.base import Canonicizer, canonicizer_registry

_PUNCTUATION_TABLE = str.maketrans("", "", string.punctuation)


@canonicizer_registry.register("strip_punctuation")
@dataclass
class StripPunctuation(Canonicizer):
    """Remove all punctuation characters from the text."""

    display_name: str = "Strip Punctuation"
    description: str = "Removes all punctuation characters."

    def process(self, text: str) -> str:
        """Return *text* with all punctuation characters removed."""
        return text.translate(_PUNCTUATION_TABLE)

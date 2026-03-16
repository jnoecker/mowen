"""Canonicizer that removes all digit characters."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.canonicizers.base import Canonicizer, canonicizer_registry

_DIGIT_TABLE = str.maketrans("", "", "0123456789")


@canonicizer_registry.register("strip_numbers")
@dataclass
class StripNumbers(Canonicizer):
    """Remove all digit characters (0-9) from the text."""

    display_name: str = "Strip Numbers"
    description: str = "Removes all digit characters (0-9)."

    def process(self, text: str) -> str:
        """Return *text* with all digit characters removed."""
        return text.translate(_DIGIT_TABLE)

"""Canonicizer that removes null and control characters."""

from __future__ import annotations

import re
from dataclasses import dataclass

from mowen.canonicizers.base import Canonicizer, canonicizer_registry

# Match control characters (ASCII 0-31) except \t (9), \n (10), \r (13).
_CONTROL_CHAR_PATTERN = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f]"
)


@canonicizer_registry.register("strip_null_chars")
@dataclass
class StripNullChars(Canonicizer):
    """Remove null characters and other control characters from the text."""

    display_name: str = "Strip Null Characters"
    description: str = (
        "Removes null characters and other control characters "
        "(ASCII 0-31 except newline, carriage return, and tab)."
    )

    def process(self, text: str) -> str:
        """Return *text* with control characters removed."""
        return _CONTROL_CHAR_PATTERN.sub("", text)

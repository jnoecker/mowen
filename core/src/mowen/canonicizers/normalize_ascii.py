"""Canonicizer that replaces common Unicode characters with ASCII equivalents."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from mowen.canonicizers.base import Canonicizer, canonicizer_registry

# Mapping of common Unicode characters to ASCII equivalents.
_UNICODE_TO_ASCII: dict[str, str] = {
    "\u2018": "'",   # left single quotation mark
    "\u2019": "'",   # right single quotation mark
    "\u201c": '"',   # left double quotation mark
    "\u201d": '"',   # right double quotation mark
    "\u2014": "-",   # em dash
    "\u2013": "-",   # en dash
    "\u2026": "...", # horizontal ellipsis
}

_UNICODE_TABLE = str.maketrans(_UNICODE_TO_ASCII)


@canonicizer_registry.register("normalize_ascii")
@dataclass
class NormalizeAscii(Canonicizer):
    """Replace common Unicode characters with ASCII equivalents."""

    display_name: str = "Normalize ASCII"
    description: str = (
        "Replaces smart quotes, em/en dashes, ellipses, and accented "
        "characters with their closest ASCII equivalents."
    )

    def process(self, text: str) -> str:
        """Return *text* with Unicode characters replaced by ASCII equivalents."""
        # First, replace well-known Unicode characters.
        text = text.translate(_UNICODE_TABLE)
        # Decompose accented characters and drop combining marks.
        text = unicodedata.normalize("NFKD", text)
        # Encode to ASCII, ignoring characters that cannot be represented.
        return text.encode("ascii", "ignore").decode("ascii")

"""Canonicizer that normalizes whitespace."""

from __future__ import annotations

import re
from dataclasses import dataclass

from mowen.canonicizers.base import Canonicizer, canonicizer_registry

_WHITESPACE_RUN = re.compile(r"\s+")


@canonicizer_registry.register("normalize_whitespace")
@dataclass
class NormalizeWhitespace(Canonicizer):
    """Collapse whitespace runs to a single space and strip edges."""

    display_name: str = "Normalize Whitespace"
    description: str = (
        "Collapses all whitespace sequences to a single space "
        "and strips leading/trailing whitespace."
    )

    def process(self, text: str) -> str:
        """Collapse whitespace runs and strip leading/trailing whitespace."""
        return _WHITESPACE_RUN.sub(" ", text).strip()

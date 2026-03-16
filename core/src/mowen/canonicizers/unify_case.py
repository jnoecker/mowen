"""Canonicizer that converts text to lowercase."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.canonicizers.base import Canonicizer, canonicizer_registry


@canonicizer_registry.register("unify_case")
@dataclass
class UnifyCase(Canonicizer):
    """Convert all characters to lowercase."""

    display_name: str = "Unify Case"
    description: str = "Converts all characters to lowercase."

    def process(self, text: str) -> str:
        """Return *text* converted to lowercase."""
        return text.lower()

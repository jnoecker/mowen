"""Smash I canonicizer — lowercase the pronoun "I" without affecting other words."""

from __future__ import annotations

import re

from mowen.canonicizers.base import Canonicizer, canonicizer_registry


@canonicizer_registry.register("smash_i")
class SmashI(Canonicizer):
    """Convert standalone "I" (first-person pronoun) to lowercase.

    Unlike ``unify_case``, this only affects the single character "I"
    when it appears as a standalone word.  All other capitalization is
    preserved.  This targets a specific English stylistic feature
    without destroying case information for other words.
    """

    display_name = "Smash I"
    description = "Lowercase the standalone pronoun 'I' only."

    def process(self, text: str) -> str:
        return re.sub(r"(?<!\w)I(?!\w)", "i", text)

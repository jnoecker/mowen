"""Prediction by Partial Matching (PPM) compression distance.

Builds a character-level statistical model from one text and computes
the cross-entropy of the other text under that model.  More principled
than gzip-based NCD as it is a proper probabilistic model.

Reference: Teahan & Harper (2003), used in PAN authorship competitions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.distance_functions.base import (
    DistanceFunction,
    distance_function_registry,
)
from mowen.parameters import ParamDef
from mowen.types import Histogram


class _PPMNode:
    """A node in the PPM context trie."""

    __slots__ = ("children", "count", "total")

    def __init__(self) -> None:
        self.children: dict[str, _PPMNode] = {}
        self.count: int = 0
        self.total: int = 0


class _PPMModel:
    """Character-level PPM model with escape-based backoff."""

    def __init__(self, order: int) -> None:
        self.order = order
        self._root = _PPMNode()
        self._alphabet_size = 0
        self._seen_chars: set[str] = set()

    def train(self, text: str) -> None:
        """Build context trie from training text."""
        self._seen_chars = set(text)
        self._alphabet_size = max(len(self._seen_chars), 1)

        for i in range(len(text)):
            node = self._root
            node.total += 1
            # Update contexts of length 0..order
            for d in range(min(self.order, i) + 1):
                start = i - d
                ctx_char = text[start] if d > 0 else ""
                if d > 0:
                    if ctx_char not in node.children:
                        node.children[ctx_char] = _PPMNode()
                    node = node.children[ctx_char]
                    node.total += 1
                # Record the predicted character
                char = text[i]
                if char not in node.children:
                    node.children[char] = _PPMNode()
                node.children[char].count += 1

    def cross_entropy(self, text: str) -> float:
        """Compute per-character cross-entropy of text under model."""
        if not text:
            return 0.0

        total_log_prob = 0.0
        eps = 1e-10

        for i, char in enumerate(text):
            # Try contexts from longest to shortest (backoff)
            prob = self._char_probability(text, i, char)
            total_log_prob += -math.log2(max(prob, eps))

        return total_log_prob / len(text)

    def _char_probability(
        self, text: str, pos: int, char: str
    ) -> float:
        """Estimate probability of char at position using backoff."""
        # Try decreasing context lengths
        for d in range(min(self.order, pos), -1, -1):
            node = self._root
            # Walk to context node
            ok = True
            for j in range(d):
                ctx_char = text[pos - d + j]
                if ctx_char in node.children:
                    node = node.children[ctx_char]
                else:
                    ok = False
                    break
            if not ok:
                continue

            if node.total > 0 and char in node.children:
                # Smoothed probability with escape
                count = node.children[char].count
                if count > 0:
                    return count / node.total

        # Fallback: uniform over observed alphabet (or 256 if empty)
        return 1.0 / (self._alphabet_size if self._alphabet_size > 0 else 256)


def _histogram_to_text(h: Histogram) -> str:
    """Reconstruct text from histogram events (frequency-weighted)."""
    tokens = []
    for event in h.unique_events():
        tokens.extend([event.data] * h.absolute_frequency(event))
    return " ".join(tokens)


@distance_function_registry.register("ppm")
@dataclass
class PPMDistance(DistanceFunction):
    """Cross-entropy distance using Prediction by Partial Matching.

    Builds a character-level PPM model from one histogram's text and
    computes the cross-entropy of the other histogram's text under it.
    Returns the average of both directions for symmetry.

    Pure Python, no external dependencies.

    Reference: Teahan & Harper (2003).
    """

    display_name: str = "PPM Compression Distance"
    description: str = (
        "Cross-entropy distance via Prediction by Partial Matching. "
        "Pure Python, no dependencies."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="order",
                description="Maximum context length for the PPM model.",
                param_type=int,
                default=5,
                min_value=1,
                max_value=16,
            ),
        ]

    def distance(self, h1: Histogram, h2: Histogram) -> float:
        """Return the symmetric PPM cross-entropy distance."""
        text1 = _histogram_to_text(h1)
        text2 = _histogram_to_text(h2)

        if not text1 or not text2:
            return 1.0

        order: int = self.get_param("order")

        # Direction 1: train on h1, test on h2
        model1 = _PPMModel(order)
        model1.train(text1)
        ce_1to2 = model1.cross_entropy(text2)

        # Direction 2: train on h2, test on h1
        model2 = _PPMModel(order)
        model2.train(text2)
        ce_2to1 = model2.cross_entropy(text1)

        # Symmetric average
        return (ce_1to2 + ce_2to1) / 2.0

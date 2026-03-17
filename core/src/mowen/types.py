"""Core data types for mowen."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True, slots=True)
class Event:
    """An immutable, hashable event extracted from text."""

    data: str

    def __str__(self) -> str:
        return self.data


class EventSet(list["Event"]):
    """An ordered sequence of Events."""

    def to_histogram(self) -> Histogram:
        h: dict[Event, int] = {}
        for event in self:
            h[event] = h.get(event, 0) + 1
        return Histogram(h)


class Histogram:
    """Frequency distribution over Events."""

    def __init__(self, counts: dict[Event, int] | None = None) -> None:
        self._counts: dict[Event, int] = dict(counts) if counts else {}
        self._total: int = sum(self._counts.values())

    @property
    def counts(self) -> Mapping[Event, int]:
        return MappingProxyType(self._counts)

    @property
    def total(self) -> int:
        return self._total

    def absolute_frequency(self, event: Event) -> int:
        return self._counts.get(event, 0)

    def relative_frequency(self, event: Event) -> float:
        if self._total == 0:
            return 0.0
        return self._counts.get(event, 0) / self._total

    def unique_events(self) -> set[Event]:
        return set(self._counts.keys())

    def normalized(self) -> dict[Event, float]:
        """Return a dict mapping each event to its relative frequency."""
        if self._total == 0:
            return {}
        return {e: c / self._total for e, c in self._counts.items()}

    def __len__(self) -> int:
        return len(self._counts)

    def __contains__(self, event: object) -> bool:
        return event in self._counts

    def __repr__(self) -> str:
        return f"Histogram({len(self._counts)} events, {self._total} total)"


class NumericEventSet(list[float]):
    """A dense numeric feature vector (e.g. from transformer embeddings).

    Unlike :class:`EventSet`, this cannot be converted to a :class:`Histogram`.
    Analysis methods that accept numeric vectors (sklearn-based) use these directly.
    """

    pass


@dataclass
class Document:
    """A text document with optional author attribution."""

    text: str
    author: str | None = None
    title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Attribution:
    """An attribution result: author with confidence score."""

    author: str
    score: float


@dataclass
class PipelineResult:
    """Result of running the pipeline on one unknown document.

    ``lower_is_better`` indicates the score semantics of the analysis
    method that produced these rankings:

    * ``True`` — distance-based methods (nearest_neighbor, centroid,
      burrows_delta): lower score = better match.
    * ``False`` — probability-based methods (svm, naive_bayes,
      markov_chain): higher score = better match.

    Rankings are always sorted best-first regardless of direction.
    """

    unknown_document: Document
    rankings: list[Attribution]
    lower_is_better: bool = True
    verification_threshold: float | None = None

    @property
    def top_author(self) -> str | None:
        return self.rankings[0].author if self.rankings else None

"""Base event culler class and registry for event culling components."""

from __future__ import annotations

import math
from abc import ABC
from dataclasses import dataclass, field
from typing import NamedTuple

from mowen.parameters import Configurable
from mowen.registry import Registry
from mowen.types import Event, EventSet


def _per_document_histograms(
    event_sets: list[EventSet],
) -> tuple[set[Event], list[dict[Event, int]]]:
    """Build per-document frequency maps and collect the union of all events.

    Returns a tuple of ``(all_events, doc_histograms)`` where *all_events* is
    the set of every :class:`Event` seen in any event set and
    *doc_histograms* is a list of ``{event: count}`` dicts, one per event set.
    """
    all_events: set[Event] = set()
    doc_histograms: list[dict[Event, int]] = []
    for event_set in event_sets:
        counts = dict(event_set.to_histogram().counts)
        doc_histograms.append(counts)
        all_events.update(counts.keys())
    return all_events, doc_histograms


def _aggregate_counts(event_sets: list[EventSet]) -> dict[Event, int]:
    """Build a combined frequency map across all event sets.

    Returns a dictionary mapping each :class:`Event` to its total count
    across every event set.
    """
    combined: dict[Event, int] = {}
    for es in event_sets:
        for event, count in es.to_histogram().counts.items():
            combined[event] = combined.get(event, 0) + count
    return combined


# --- Statistical helpers for cullers ---


class EventStats(NamedTuple):
    """Per-event statistics across documents."""

    counts: list[int]
    mean: float
    variance: float
    std_dev: float


def _compute_event_stats(
    all_events: set[Event],
    doc_histograms: list[dict[Event, int]],
) -> dict[Event, EventStats]:
    """Compute mean, variance, and std_dev per event across documents."""
    n_docs = len(doc_histograms)
    result: dict[Event, EventStats] = {}
    for event in all_events:
        counts = [h.get(event, 0) for h in doc_histograms]
        mean = sum(counts) / n_docs
        variance = sum((c - mean) ** 2 for c in counts) / n_docs
        result[event] = EventStats(counts, mean, variance, math.sqrt(variance))
    return result


def _top_n_events(
    event_scores: dict[Event, float],
    n: int,
) -> set[Event]:
    """Return the top *n* events ranked by score (descending)."""
    ranked = sorted(event_scores, key=lambda e: event_scores[e], reverse=True)
    return set(ranked[:n])


@dataclass
class EventCuller(ABC, Configurable):
    """Abstract base class for all event cullers.

    An event culler filters event sets by removing events that do not meet
    some criterion (e.g. rarity, frequency threshold).  Subclasses must
    set the ``display_name`` and ``description`` class attributes.

    The two-phase interface works as follows:

    1. :meth:`init` is called once with the event sets from **known
       documents only** so the culler can compute corpus-wide statistics
       without leaking information from unknown documents.
    2. :meth:`cull` is called once per event set (known and unknown) to
       produce a filtered version.

    Subclasses should populate :attr:`_kept_events` in their :meth:`init`
    method.  The default :meth:`cull` implementation filters based on that
    set.  Subclasses may still override :meth:`cull` if they need custom
    filtering logic.
    """

    display_name: str = ""
    description: str = ""
    _kept_events: set[Event] | None = field(default=None, init=False, repr=False)

    def init(self, event_sets: list[EventSet]) -> None:
        """Compute corpus-wide statistics from all event sets.

        Called once before any calls to :meth:`cull`.  The default
        implementation is a no-op; override in subclasses that need
        global information (e.g. combined frequency counts).

        Parameters
        ----------
        event_sets:
            Event sets from the known documents in the corpus.
        """

    def cull(self, event_set: EventSet) -> EventSet:
        """Filter *event_set*, keeping only events that pass the culler.

        Parameters
        ----------
        event_set:
            The event set to filter.

        Returns
        -------
        EventSet
            A new event set containing only the events that survived
            culling, preserving the original order.
        """
        if self._kept_events is None:
            return event_set
        return EventSet(e for e in event_set if e in self._kept_events)


event_culler_registry: Registry[EventCuller] = Registry[EventCuller]("event_culler")

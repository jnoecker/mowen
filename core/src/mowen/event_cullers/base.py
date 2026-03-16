"""Base event culler class and registry for event culling components."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field

from mowen.parameters import Configurable
from mowen.registry import Registry
from mowen.types import Event, EventSet


def _aggregate_counts(event_sets: list[EventSet]) -> dict[Event, int]:
    """Build a combined frequency map across all event sets.

    Returns a dictionary mapping each :class:`Event` to its total count
    across every event set.
    """
    combined: dict[Event, int] = {}
    for es in event_sets:
        for event, count in es.to_histogram()._counts.items():
            combined[event] = combined.get(event, 0) + count
    return combined


@dataclass
class EventCuller(ABC, Configurable):
    """Abstract base class for all event cullers.

    An event culler filters event sets by removing events that do not meet
    some criterion (e.g. rarity, frequency threshold).  Subclasses must
    set the ``display_name`` and ``description`` class attributes.

    The two-phase interface works as follows:

    1. :meth:`init` is called once with every event set in the corpus
       (both known and unknown documents) so the culler can compute
       corpus-wide statistics.
    2. :meth:`cull` is called once per event set to produce a filtered
       version.

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
            Every event set in the corpus (known and unknown documents).
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

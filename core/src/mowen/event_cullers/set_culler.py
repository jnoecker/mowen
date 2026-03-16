"""Set culler — deduplicate events (remove frequency information)."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_cullers.base import EventCuller, event_culler_registry
from mowen.types import Event, EventSet


@event_culler_registry.register("set_culler")
@dataclass
class SetCuller(EventCuller):
    """Remove duplicate events, keeping only the first occurrence of each.

    Converts the event sequence to a set, discarding frequency
    information.  Useful for presence/absence analysis rather than
    frequency-based analysis.
    """

    display_name = "Set Culler"
    description = "Remove duplicate events (keep first occurrence only)."

    def cull(self, event_set: EventSet) -> EventSet:
        seen: set[Event] = set()
        result = EventSet()
        for event in event_set:
            if event not in seen:
                seen.add(event)
                result.append(event)
        return result

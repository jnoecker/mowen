"""Event culler that keeps events appearing in a specified document count range."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_cullers.base import EventCuller, event_culler_registry
from mowen.parameters import ParamDef
from mowen.types import Event, EventSet


@event_culler_registry.register("range")
@dataclass
class RangeCuller(EventCuller):
    """Keep events that appear in at least *min_count* and at most *max_count* documents.

    During :meth:`init`, the number of event sets (documents) each event
    appears in is counted.  During :meth:`cull`, only events whose document
    count falls within ``[min_count, max_count]`` are retained.
    """

    display_name: str = "Document Range"
    description: str = (
        "Retains events that appear in a number of documents within "
        "the specified range."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="min_count",
                description="Minimum number of documents an event must appear in.",
                param_type=int,
                default=2,
                min_value=1,
            ),
            ParamDef(
                name="max_count",
                description="Maximum number of documents an event may appear in.",
                param_type=int,
                default=100,
                min_value=1,
            ),
        ]

    def init(self, event_sets: list[EventSet]) -> None:
        """Count document frequency for each event and select those in range."""
        doc_freq: dict[Event, int] = {}
        for event_set in event_sets:
            seen = event_set.to_histogram().unique_events()
            for event in seen:
                doc_freq[event] = doc_freq.get(event, 0) + 1

        min_count: int = self.get_param("min_count")
        max_count: int = self.get_param("max_count")
        self._kept_events = {
            event
            for event, count in doc_freq.items()
            if min_count <= count <= max_count
        }

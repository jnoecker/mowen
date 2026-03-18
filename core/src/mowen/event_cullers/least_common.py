"""Event culler that keeps only the N least common events across the corpus."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_cullers.base import (
    EventCuller,
    _aggregate_counts,
    event_culler_registry,
)
from mowen.parameters import ParamDef
from mowen.types import EventSet


@event_culler_registry.register("least_common")
@dataclass
class LeastCommon(EventCuller):
    """Keep only the *N* least frequent events in the corpus.

    During :meth:`init`, a combined histogram is built from every event set
    and the bottom-*N* events are identified.  During :meth:`cull`, only events
    present in that bottom-*N* set are retained.
    """

    display_name: str = "Least Common Events"
    description: str = "Retains only the N least frequent events across all documents."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="n",
                description="Number of least common events to keep.",
                param_type=int,
                default=50,
                min_value=1,
            ),
        ]

    def init(self, event_sets: list[EventSet]) -> None:
        """Build a corpus-wide histogram and select the bottom-N events."""
        combined = _aggregate_counts(event_sets)

        n: int = self.get_param("n")
        ranked = sorted(combined, key=lambda e: combined[e])
        self._kept_events = set(ranked[:n])

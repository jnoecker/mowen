"""Craig's Zeta event culler."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_cullers.base import EventCuller, event_culler_registry
from mowen.parameters import ParamDef
from mowen.types import Event, EventSet


@event_culler_registry.register("zeta")
@dataclass
class ZetaCuller(EventCuller):
    """Craig's Zeta feature selection.

    For each event, computes the proportion of documents in the
    *primary* author group that contain it minus the proportion of
    documents in all *other* author groups that contain it:

        zeta(w) = dp(w) - do(w)

    Events with high positive zeta are preferred by the primary author;
    high negative zeta are avoided.  Keeps events where |zeta| >= the
    threshold.

    The ``primary_author`` parameter selects which author is the
    "target" — all others form the contrast set.  If not set, the
    author with the most documents is used.

    Reference: Craig & Kinney, "Shakespeare, Computers, and the
    Mystery of Authorship" (2009).  Eder, "Rolling Stylometry" (2015).
    """

    display_name: str = "Craig's Zeta"
    description: str = (
        "Select features preferred or avoided by a target author (Craig's Zeta)."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="threshold",
                description="Minimum |zeta| score to keep an event.",
                param_type=float,
                default=0.3,
                min_value=0.0,
                max_value=1.0,
            ),
            ParamDef(
                name="primary_author",
                description="Target author name (default: most documents).",
                param_type=str,
                default="",
            ),
        ]

    def cull(
        self,
        event_sets: list[EventSet],
        authors: list[str],
    ) -> set[Event]:
        """Return the set of events to *keep*."""
        threshold: float = self.get_param("threshold")
        primary: str = self.get_param("primary_author")

        if not event_sets:
            return set()

        # Pick primary author.
        if not primary:
            counts: dict[str, int] = {}
            for a in authors:
                counts[a] = counts.get(a, 0) + 1
            primary = max(counts, key=lambda a: counts[a])

        # Split into primary vs. other document groups.
        primary_sets = [es for es, a in zip(event_sets, authors) if a == primary]
        other_sets = [es for es, a in zip(event_sets, authors) if a != primary]

        if not primary_sets or not other_sets:
            # Can't compute zeta with only one group — keep everything.
            all_events: set[Event] = set()
            for es in event_sets:
                all_events.update(es)
            return all_events

        # Collect all unique events.
        all_events_set: set[Event] = set()
        for es in event_sets:
            all_events_set.update(es)

        # For each event, compute document-presence proportions.
        keep: set[Event] = set()
        n_primary = len(primary_sets)
        n_other = len(other_sets)

        for event in all_events_set:
            dp = sum(1 for es in primary_sets if event in es) / n_primary
            do = sum(1 for es in other_sets if event in es) / n_other
            zeta = dp - do
            if abs(zeta) >= threshold:
                keep.add(event)

        return keep

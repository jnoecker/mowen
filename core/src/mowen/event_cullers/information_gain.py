"""Event culler that keeps top-N events ranked by frequency entropy across documents."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.event_cullers.base import EventCuller, _per_document_histograms, event_culler_registry
from mowen.parameters import ParamDef
from mowen.types import Event, EventSet


@event_culler_registry.register("information_gain")
@dataclass
class InformationGain(EventCuller):
    """Keep the top-*N* events ranked by entropy of their frequency distribution.

    Since author labels are not available at the culler level, this uses a
    proxy for information gain: the entropy of each event's frequency
    distribution across documents.  Events with higher entropy (more variable
    across documents) tend to be more discriminating for authorship.

    During :meth:`init`, for each unique event a probability distribution
    over documents is formed from its per-document counts and the Shannon
    entropy is computed.  The top-*N* events by entropy are retained.
    """

    display_name: str = "Information Gain"
    description: str = (
        "Retains the top N events ranked by the entropy of their "
        "frequency distribution across documents."
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="n",
                description="Number of top events by entropy to keep.",
                param_type=int,
                default=50,
                min_value=1,
            ),
        ]

    @staticmethod
    def _entropy(counts: list[int]) -> float:
        """Compute Shannon entropy of a distribution given raw counts."""
        total = sum(counts)
        if total == 0:
            return 0.0
        ent = 0.0
        for c in counts:
            if c > 0:
                p = c / total
                ent -= p * math.log2(p)
        return ent

    def init(self, event_sets: list[EventSet]) -> None:
        """Compute per-event entropy across documents and select top-N."""
        all_events, doc_histograms = _per_document_histograms(event_sets)

        if not all_events or not doc_histograms:
            self._kept_events = set()
            return

        # Compute entropy for each event across documents.
        event_entropy: dict[Event, float] = {}
        for event in all_events:
            per_doc = [h.get(event, 0) for h in doc_histograms]
            event_entropy[event] = self._entropy(per_doc)

        n: int = self.get_param("n")
        ranked = sorted(event_entropy, key=lambda e: event_entropy[e], reverse=True)
        self._kept_events = set(ranked[:n])

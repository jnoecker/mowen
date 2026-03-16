"""Thin Cross-Entropy (ThinXent) analysis method."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field

from mowen.analysis_methods.base import AnalysisMethod, analysis_method_registry
from mowen.parameters import ParamDef
from mowen.types import Attribution, Document, Event, Histogram


@analysis_method_registry.register("thin_xent")
@dataclass
class ThinCrossEntropy(AnalysisMethod):
    """Attribute authorship using thin cross-entropy over event transitions.

    Builds a first-order Markov transition model for each author from
    their training events.  For the unknown document, computes the
    cross-entropy of the event sequence under each author's model.
    Lower cross-entropy indicates a better fit.

    The transition probabilities use Laplace smoothing to handle unseen
    transitions.

    Score semantics: lower = better match (cross-entropy-based).
    """

    display_name: str = "Thin Cross-Entropy"
    description: str = (
        "Authorship via cross-entropy of event transition sequences."
    )

    _author_transitions: dict[str, dict[Event, dict[Event, float]]] = field(
        default_factory=dict, init=False, repr=False,
    )
    _vocab_size: int = field(default=0, init=False, repr=False)

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="window",
                description="Sliding window size for entropy calculation.",
                param_type=int,
                default=15,
                min_value=2,
                max_value=100,
            ),
        ]

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Build per-author transition probability models."""
        super().train(known_docs)

        # Collect per-author event sequences from histograms.
        # We reconstruct an approximate sequence by repeating events
        # according to their counts in a deterministic order.
        global_vocab: set[Event] = set()
        author_sequences: dict[str, list[Event]] = defaultdict(list)

        for doc, hist in self._known_docs:
            author = doc.author or ""
            for event in sorted(hist.unique_events(), key=lambda e: e.data):
                count = hist.absolute_frequency(event)
                author_sequences[author].extend([event] * count)
                global_vocab.add(event)

        self._vocab_size = len(global_vocab)

        # Build transition counts and smooth probabilities.
        self._author_transitions = {}
        for author, seq in author_sequences.items():
            trans_counts: dict[Event, dict[Event, int]] = defaultdict(
                lambda: defaultdict(int)
            )
            for i in range(len(seq) - 1):
                trans_counts[seq[i]][seq[i + 1]] += 1

            # Convert to probabilities with Laplace smoothing.
            trans_probs: dict[Event, dict[Event, float]] = {}
            for from_event, to_counts in trans_counts.items():
                total = sum(to_counts.values())
                denom = total + self._vocab_size
                probs: dict[Event, float] = {}
                for to_event in global_vocab:
                    probs[to_event] = (to_counts.get(to_event, 0) + 1) / denom
                trans_probs[from_event] = probs
            self._author_transitions[author] = trans_probs

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions ranked by cross-entropy (lowest first)."""
        if not self._author_transitions:
            return []

        window: int = self.get_param("window")

        # Reconstruct unknown event sequence from histogram.
        unknown_seq: list[Event] = []
        for event in sorted(unknown_histogram.unique_events(), key=lambda e: e.data):
            count = unknown_histogram.absolute_frequency(event)
            unknown_seq.extend([event] * count)

        if len(unknown_seq) < 2:
            # Can't compute transitions; return equal scores.
            return [
                Attribution(author=a, score=0.0)
                for a in self._author_transitions
            ]

        attributions: list[Attribution] = []
        for author, trans_probs in self._author_transitions.items():
            # Compute cross-entropy over sliding windows.
            total_log_prob = 0.0
            n_transitions = 0
            oov_prob = 1.0 / (self._vocab_size + 1)

            for i in range(len(unknown_seq) - 1):
                from_event = unknown_seq[i]
                to_event = unknown_seq[i + 1]
                if from_event in trans_probs:
                    prob = trans_probs[from_event].get(to_event, oov_prob)
                else:
                    prob = oov_prob
                total_log_prob += math.log2(prob)
                n_transitions += 1

            # Cross-entropy = negative mean log probability.
            xent = -total_log_prob / n_transitions if n_transitions > 0 else float("inf")
            attributions.append(Attribution(author=author, score=xent))

        attributions.sort(key=lambda a: a.score)
        return attributions

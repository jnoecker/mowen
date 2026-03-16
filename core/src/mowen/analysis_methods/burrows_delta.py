"""Burrows' Delta analysis method."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from mowen.analysis_methods.base import AnalysisMethod, analysis_method_registry
from mowen.parameters import ParamDef
from mowen.types import Attribution, Document, Event, Histogram


@analysis_method_registry.register("burrows_delta")
@dataclass
class BurrowsDelta(AnalysisMethod):
    """Attribute authorship using Burrows' Delta.

    Burrows' Delta is a distance measure that standardises feature
    frequencies by their corpus-wide mean and standard deviation.  For
    each candidate author the delta is the mean of the absolute
    z-score differences across features.  The author with the lowest
    delta is the best match.

    Only the top *n_features* most frequent events in the corpus are
    used.

    Score semantics: lower = better match (distance-based).
    """

    display_name: str = "Burrows' Delta"
    description: str = (
        "Assigns authorship using Burrows' Delta — a z-score based "
        "distance measure over the most frequent features."
    )

    _event_mean: dict[Event, float] = field(
        default_factory=dict, init=False, repr=False,
    )
    _event_std: dict[Event, float] = field(
        default_factory=dict, init=False, repr=False,
    )
    _features: list[Event] = field(
        default_factory=list, init=False, repr=False,
    )
    _author_profiles: dict[str, dict[Event, float]] = field(
        default_factory=dict, init=False, repr=False,
    )
    _author_z_profiles: dict[str, dict[Event, float]] = field(
        default_factory=dict, init=False, repr=False,
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        """Declare the n_features parameter."""
        return [
            ParamDef(
                name="n_features",
                description="Number of top-frequency events to use.",
                param_type=int,
                default=100,
                min_value=1,
            ),
        ]

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Compute corpus-wide z-score statistics and per-author profiles."""
        super().train(known_docs)

        n_features: int = self.get_param("n_features")

        # Collect all relative frequencies per event across all documents.
        event_freqs: dict[Event, list[float]] = defaultdict(list)
        all_events: dict[Event, float] = defaultdict(float)
        n_docs = len(self._known_docs)

        for _doc, hist in self._known_docs:
            seen: set[Event] = set()
            for event in hist.unique_events():
                freq = hist.relative_frequency(event)
                event_freqs[event].append(freq)
                all_events[event] += freq
                seen.add(event)

        # Pad unseen events with 0.0 so every event has n_docs entries.
        for event in event_freqs:
            while len(event_freqs[event]) < n_docs:
                event_freqs[event].append(0.0)

        # Select top n_features by corpus-wide total frequency.
        sorted_events = sorted(all_events, key=lambda e: all_events[e], reverse=True)
        self._features = sorted_events[:n_features]

        # Compute mean and std for selected features, dropping zero-variance
        # features (they carry no discriminative information).
        self._event_mean = {}
        self._event_std = {}
        kept: list[Event] = []
        for event in self._features:
            freqs = event_freqs[event]
            mean = sum(freqs) / len(freqs)
            variance = sum((f - mean) ** 2 for f in freqs) / len(freqs)
            std = math.sqrt(variance)
            if std > 0:
                self._event_mean[event] = mean
                self._event_std[event] = std
                kept.append(event)
        self._features = kept

        # Build per-author profiles: average relative frequency across author's docs.
        author_freq_sums: dict[str, dict[Event, float]] = defaultdict(
            lambda: defaultdict(float),
        )
        author_doc_counts: dict[str, int] = defaultdict(int)

        for doc, hist in self._known_docs:
            author = doc.author or ""
            author_doc_counts[author] += 1
            for event in self._features:
                author_freq_sums[author][event] += hist.relative_frequency(event)

        self._author_profiles = {}
        for author, sums in author_freq_sums.items():
            n = author_doc_counts[author]
            self._author_profiles[author] = {
                event: sums[event] / n for event in self._features
            }

        # Pre-compute z-score profiles for each author's centroid.
        self._author_z_profiles = {}
        for author, profile in self._author_profiles.items():
            self._author_z_profiles[author] = {
                event: (profile[event] - self._event_mean[event]) / self._event_std[event]
                for event in self._features
            }

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions ranked by Burrows' Delta (lowest first)."""
        if not self._features:
            return []

        # Z-scores for the unknown document.
        z_unknown: dict[Event, float] = {}
        for event in self._features:
            freq = unknown_histogram.relative_frequency(event)
            z_unknown[event] = (freq - self._event_mean[event]) / self._event_std[event]

        attributions: list[Attribution] = []
        for author, z_profile in self._author_z_profiles.items():
            delta = 0.0
            for event in self._features:
                delta += abs(z_unknown[event] - z_profile[event])
            delta /= len(self._features)
            attributions.append(Attribution(author=author, score=delta))

        attributions.sort(key=lambda a: a.score)
        return attributions

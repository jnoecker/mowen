"""Eder's Delta analysis method."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mowen.analysis_methods.base import AnalysisMethod, analysis_method_registry
from mowen.parameters import ParamDef
from mowen.types import Attribution, Event, Histogram


@analysis_method_registry.register("eders_delta")
@dataclass
class EdersDelta(AnalysisMethod):
    """Eder's Delta.

    A variant of Burrows' Delta that:
    1. Uses only the top-N most frequent features (across all documents).
    2. Applies square-root transformation to relative frequencies
       before z-score normalisation.

    The sqrt transform compresses high-frequency features and expands
    low-frequency ones, reducing the outsized influence of the most
    common words.

    Score semantics: lower = better match (distance-based).

    Reference: Eder, "Does Size Matter? Authorship Attribution,
    Small Samples, Big Problem" (DSH, 2015).
    """

    display_name: str = "Eder's Delta"
    description: str = (
        "Eder's Delta: sqrt-transformed z-score distance with top-N feature selection."
    )
    lower_is_better: bool = True

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="top_n",
                description="Number of most frequent features to use (0 = all).",
                param_type=int,
                default=100,
                min_value=0,
                max_value=10000,
            ),
        ]

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions ranked by Eder's Delta distance."""
        top_n: int = self.get_param("top_n")

        # Collect all events and their total frequencies.
        event_freq: dict[Event, int] = {}
        all_hists = [h for _, h in self._known_docs]
        all_hists.append(unknown_histogram)

        for h in all_hists:
            for e in h.unique_events():
                event_freq[e] = event_freq.get(e, 0) + h.absolute_frequency(e)

        # Select top-N features by total frequency.
        if top_n > 0 and len(event_freq) > top_n:
            sorted_events = sorted(
                event_freq, key=lambda e: event_freq[e], reverse=True
            )
            features = sorted_events[:top_n]
        else:
            features = sorted(event_freq, key=str)

        n_features = len(features)
        if n_features == 0:
            return []

        # Extract sqrt-transformed relative frequencies for all known docs.
        def _sqrt_freqs(h: Histogram) -> list[float]:
            return [math.sqrt(h.relative_frequency(e)) for e in features]

        known_vectors = [_sqrt_freqs(h) for _, h in self._known_docs]

        # Compute mean and std per feature across known docs.
        n_docs = len(known_vectors)
        means = [0.0] * n_features
        for vec in known_vectors:
            for i, v in enumerate(vec):
                means[i] += v
        means = [m / n_docs for m in means]

        stds = [0.0] * n_features
        for vec in known_vectors:
            for i, v in enumerate(vec):
                stds[i] += (v - means[i]) ** 2
        stds = [math.sqrt(s / max(n_docs - 1, 1)) for s in stds]

        # Z-score transform.
        def _z_scores(vec: list[float]) -> list[float]:
            return [
                (v - means[i]) / stds[i] if stds[i] > 0 else 0.0
                for i, v in enumerate(vec)
            ]

        known_z = [_z_scores(v) for v in known_vectors]
        unknown_z = _z_scores(_sqrt_freqs(unknown_histogram))

        # Compute mean z-score vector per author.
        author_indices: dict[str, list[int]] = {}
        for idx, (doc, _) in enumerate(self._known_docs):
            author = doc.author or ""
            if author not in author_indices:
                author_indices[author] = []
            author_indices[author].append(idx)

        attributions = []
        for author, indices in author_indices.items():
            # Author centroid in z-score space.
            centroid = [0.0] * n_features
            for idx in indices:
                for i, v in enumerate(known_z[idx]):
                    centroid[i] += v
            centroid = [c / len(indices) for c in centroid]

            # Manhattan distance in z-score space.
            delta = sum(abs(unknown_z[i] - centroid[i]) for i in range(n_features))
            delta /= n_features  # normalise by feature count
            attributions.append(Attribution(author=author, score=delta))

        attributions.sort(key=lambda a: a.score)
        return attributions

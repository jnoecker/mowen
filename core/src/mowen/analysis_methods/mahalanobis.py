"""Mahalanobis distance analysis method."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.analysis_methods.base import AnalysisMethod, analysis_method_registry
from mowen.types import Attribution, Histogram


@analysis_method_registry.register("mahalanobis")
@dataclass
class MahalanobisDistance(AnalysisMethod):
    """Mahalanobis distance analysis method.

    Computes the generalised squared interpoint distance between the
    unknown document and each author's centroid, accounting for
    feature covariance.  Requires numpy (raises ImportError if absent).

    Score semantics: lower = better match (distance-based).
    """

    display_name: str = "Mahalanobis Distance"
    description: str = (
        "Mahalanobis distance to each author centroid, accounting for "
        "feature covariance."
    )
    lower_is_better: bool = True

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions ranked by Mahalanobis distance."""
        try:
            import numpy as np  # type: ignore[import-untyped]
            from numpy.linalg import LinAlgError, pinv  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError(
                "MahalanobisDistance requires numpy. "
                "Install it with: pip install numpy"
            )

        # Collect all events across all known documents.
        all_events_set: set = set()
        for _doc, hist in self._known_docs:
            all_events_set |= hist.unique_events()
        all_events_set |= unknown_histogram.unique_events()
        all_events = sorted(all_events_set, key=str)
        n_features = len(all_events)

        if n_features == 0:
            return []

        event_idx = {e: i for i, e in enumerate(all_events)}

        def _to_vector(h: Histogram) -> "np.ndarray":
            v = np.zeros(n_features)
            for e in h.unique_events():
                v[event_idx[e]] = h.relative_frequency(e)
            return v

        # Build per-author centroids and collect all vectors for covariance.
        author_vectors: dict[str, list] = {}
        for doc, hist in self._known_docs:
            author = doc.author or ""
            if author not in author_vectors:
                author_vectors[author] = []
            author_vectors[author].append(_to_vector(hist))

        # Compute pooled covariance matrix across all known documents.
        all_vectors = np.array([v for vecs in author_vectors.values() for v in vecs])
        mean = all_vectors.mean(axis=0)
        centered = all_vectors - mean
        cov = (centered.T @ centered) / max(len(all_vectors) - 1, 1)
        # Use pseudo-inverse for singular matrices.
        try:
            cov_inv = np.linalg.inv(cov)
        except LinAlgError:
            import warnings
            warnings.warn(
                "Covariance matrix is singular (insufficient data or "
                "redundant features). Falling back to pseudo-inverse.",
                stacklevel=2,
            )
            cov_inv = pinv(cov)

        unknown_vec = _to_vector(unknown_histogram)

        # Compute Mahalanobis distance to each author centroid.
        attributions = []
        for author, vecs in author_vectors.items():
            centroid = np.mean(vecs, axis=0)
            diff = unknown_vec - centroid
            dist = float(np.sqrt(diff @ cov_inv @ diff))
            attributions.append(Attribution(author=author, score=dist))

        attributions.sort(key=lambda a: a.score)
        return attributions

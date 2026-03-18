"""Contrastive learning analysis method for embedding-based attribution.

Computes author centroids in embedding space and optionally learns a
linear projection via contrastive loss to improve separation between
authors.  Works with NumericEventSet inputs from embedding drivers.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from mowen.analysis_methods.base import AnalysisMethod, analysis_method_registry
from mowen.parameters import ParamDef
from mowen.types import Attribution, Document, Histogram, NumericEventSet


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a < 1e-12 or norm_b < 1e-12:
        return 0.0
    return dot / (norm_a * norm_b)


@analysis_method_registry.register("contrastive")
@dataclass
class ContrastiveLearning(AnalysisMethod):
    """Attribute authorship using contrastive metric learning.

    Computes author centroids from embedding vectors (NumericEventSet)
    and ranks candidates by cosine similarity.  Optionally learns a
    linear projection via contrastive loss to improve author separation.

    Requires numeric event sets (transformer or SELMA embeddings).
    Projection learning requires scikit-learn.

    Score semantics: higher = more likely same author (similarity-based).
    """

    lower_is_better: bool = False

    display_name: str = "Contrastive Learning"
    description: str = (
        "Contrastive metric learning on document embeddings. "
        "Works with numeric event sets (requires scikit-learn)."
    )

    _centroids: dict[str, list[float]] = field(
        default_factory=dict, init=False, repr=False,
    )
    _projection: Any = field(default=None, init=False, repr=False)
    _dim: int = field(default=0, init=False, repr=False)
    _vocabulary: list[Any] = field(
        default_factory=list, init=False, repr=False,
    )
    _numeric_mode: bool = field(default=False, init=False, repr=False)

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="projection_dim",
                description=(
                    "Dimension of learned projection (0 = no projection, "
                    "use raw cosine similarity to centroids)."
                ),
                param_type=int,
                default=0,
                min_value=0,
                max_value=4096,
            ),
            ParamDef(
                name="n_epochs",
                description="Training epochs for projection learning.",
                param_type=int,
                default=50,
                min_value=1,
                max_value=1000,
            ),
            ParamDef(
                name="learning_rate",
                description="Learning rate for projection SGD.",
                param_type=float,
                default=0.01,
                min_value=1e-6,
                max_value=10.0,
            ),
            ParamDef(
                name="random_seed",
                description=(
                    "Random seed for reproducibility "
                    "(0 = non-deterministic)."
                ),
                param_type=int,
                default=0,
            ),
        ]

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Compute author centroids and optionally learn a projection."""
        super().train(known_docs)

        # Group vectors by author
        self._numeric_mode = any(
            isinstance(h, NumericEventSet) for _, h in self._known_docs
        )

        author_vecs: dict[str, list[list[float]]] = defaultdict(list)

        if self._numeric_mode:
            for doc, hist_or_vec in self._known_docs:
                author = doc.author or ""
                author_vecs[author].append(list(hist_or_vec))
        else:
            # Build shared vocabulary from all histograms
            from mowen.types import Event
            vocab_set: set[Event] = set()
            for _, hist in self._known_docs:
                vocab_set.update(hist.unique_events())
            self._vocabulary = sorted(vocab_set, key=lambda e: e.data)

            for doc, hist in self._known_docs:
                author = doc.author or ""
                author_vecs[author].append([
                    hist.relative_frequency(e) for e in self._vocabulary
                ])

        if not author_vecs:
            return

        # Compute raw centroids
        self._dim = len(next(iter(next(iter(author_vecs.values())))))
        raw_centroids: dict[str, list[float]] = {}
        for author, vecs in author_vecs.items():
            centroid = [0.0] * self._dim
            for v in vecs:
                for i, val in enumerate(v):
                    centroid[i] += val
            n = len(vecs)
            raw_centroids[author] = [c / n for c in centroid]

        proj_dim: int = self.get_param("projection_dim")
        if proj_dim > 0:
            self._learn_projection(author_vecs, proj_dim)
            # Re-compute centroids in projected space
            self._centroids = {}
            for author, vecs in author_vecs.items():
                projected = [self._project(v) for v in vecs]
                centroid = [0.0] * proj_dim
                for pv in projected:
                    for i, val in enumerate(pv):
                        centroid[i] += val
                n = len(projected)
                self._centroids[author] = [c / n for c in centroid]
        else:
            self._centroids = raw_centroids
            self._projection = None

    def _learn_projection(
        self,
        author_vecs: dict[str, list[list[float]]],
        proj_dim: int,
    ) -> None:
        """Learn a linear projection using contrastive pairs."""
        try:
            import numpy as np
        except ImportError as exc:
            raise ImportError(
                "Contrastive projection learning requires numpy. "
                "Install with: pip install numpy"
            ) from exc

        seed: int = self.get_param("random_seed")
        n_epochs: int = self.get_param("n_epochs")
        lr: float = self.get_param("learning_rate")

        rng = np.random.default_rng(seed if seed != 0 else None)

        # Initialize projection matrix
        w = rng.standard_normal((self._dim, proj_dim)).astype(
            np.float32
        ) * 0.01
        self._projection = w

        # Build pair lists
        authors = list(author_vecs.keys())
        all_vecs = []
        all_labels = []
        for author, vecs in author_vecs.items():
            for v in vecs:
                all_vecs.append(np.array(v, dtype=np.float32))
                all_labels.append(author)

        n = len(all_vecs)
        if n < 2:
            return

        for _ in range(n_epochs):
            # Sample random pairs
            idx_a = rng.integers(0, n)
            idx_b = rng.integers(0, n)
            if idx_a == idx_b:
                continue

            va = all_vecs[idx_a]
            vb = all_vecs[idx_b]
            same = all_labels[idx_a] == all_labels[idx_b]

            # Project
            pa = va @ w
            pb = vb @ w

            # Cosine similarity gradient update
            diff = pa - pb
            dist_sq = float(np.sum(diff ** 2))

            if same:
                # Pull together: minimize distance
                grad = 2 * np.outer(va - vb, diff)
            else:
                # Push apart: maximize distance (up to margin)
                margin = 1.0
                if dist_sq < margin:
                    grad = -2 * np.outer(va - vb, diff)
                else:
                    continue

            w -= lr * grad
            self._projection = w

    def _project(self, vec: list[float]) -> list[float]:
        """Project a vector through the learned projection."""
        if self._projection is None:
            return vec
        import numpy as np
        v = np.array(vec, dtype=np.float32)
        return (v @ self._projection).tolist()

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions ranked by similarity to centroids."""
        if isinstance(unknown_histogram, NumericEventSet):
            vec = list(unknown_histogram)
        else:
            vec = [
                unknown_histogram.relative_frequency(e)
                for e in self._vocabulary
            ]

        if self._projection is not None:
            vec = self._project(vec)

        attributions = [
            Attribution(
                author=author,
                score=_cosine_sim(vec, centroid),
            )
            for author, centroid in self._centroids.items()
        ]
        attributions.sort(key=lambda a: a.score, reverse=True)
        return attributions

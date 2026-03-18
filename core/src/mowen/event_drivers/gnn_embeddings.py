"""GNN syntactic embedding driver.

Parses text into a dependency graph via spaCy, encodes node features
(token vectors, POS, dependency relation), and applies a simple Graph
Convolutional Network to produce a document-level embedding.

The GCN uses fixed random weights (Weisfeiler-Leman style feature
extraction) — no training required.

Reference: Valdez Valenzuela et al. (PAN 2023/2025).
"""

from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import dataclass, field
from typing import Any

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.types import NumericEventSet

logger = logging.getLogger(__name__)


def _relu(x: float) -> float:
    return max(0.0, x)


def _seeded_random(seed: int, count: int) -> list[float]:
    """Generate deterministic pseudo-random floats from a seed."""
    values = []
    for i in range(count):
        h = hashlib.md5(f"{seed}:{i}".encode()).hexdigest()
        # Map hash to float in [-1, 1]
        val = (int(h[:8], 16) / 0xFFFFFFFF) * 2 - 1
        values.append(val)
    return values


class _SimpleGCN:
    """Minimal Graph Convolutional Network (pure Python, no torch).

    Uses fixed random weights as a feature extractor (no training).
    Performs message passing: for each node, aggregate neighbor features
    and apply a linear transform + ReLU.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        n_layers: int,
        seed: int,
    ) -> None:
        self.layers: list[list[list[float]]] = []
        self.biases: list[list[float]] = []
        dims = [input_dim] + [hidden_dim] * n_layers

        rng_offset = 0
        for layer_idx in range(n_layers):
            in_d = dims[layer_idx]
            out_d = dims[layer_idx + 1]
            # Xavier-like initialization
            scale = 1.0 / math.sqrt(in_d)
            raw = _seeded_random(seed + rng_offset, in_d * out_d)
            w = [
                [raw[i * out_d + j] * scale for j in range(out_d)] for i in range(in_d)
            ]
            self.layers.append(w)
            bias = [0.0] * out_d
            self.biases.append(bias)
            rng_offset += in_d * out_d

    def forward(
        self,
        node_features: list[list[float]],
        edges: list[tuple[int, int]],
    ) -> list[list[float]]:
        """Run GCN layers, return node embeddings."""
        n_nodes = len(node_features)
        if n_nodes == 0:
            return []

        # Build adjacency list (add self-loops)
        adj: dict[int, list[int]] = {i: [i] for i in range(n_nodes)}
        for src, dst in edges:
            if src < n_nodes and dst < n_nodes:
                adj.setdefault(src, []).append(dst)
                adj.setdefault(dst, []).append(src)

        h = [list(f) for f in node_features]

        for layer_w, layer_b in zip(self.layers, self.biases):
            out_dim = len(layer_w[0]) if layer_w else 0
            new_h: list[list[float]] = []

            for i in range(n_nodes):
                # Aggregate neighbor features (mean)
                neighbors = adj.get(i, [i])
                agg = [0.0] * len(h[0])
                for nb in neighbors:
                    for d in range(len(h[0])):
                        agg[d] += h[nb][d]
                n_nb = len(neighbors)
                if n_nb > 0:
                    agg = [v / n_nb for v in agg]

                # Linear transform + ReLU
                out = [0.0] * out_dim
                for j in range(out_dim):
                    val = layer_b[j]
                    for d in range(len(agg)):
                        val += agg[d] * layer_w[d][j]
                    out[j] = _relu(val)
                new_h.append(out)

            h = new_h

        return h


@event_driver_registry.register("gnn_embeddings")
@dataclass
class GNNEmbeddingDriver(EventDriver):
    """Produce embeddings from syntactic dependency graphs via GCN.

    Parses text with spaCy, builds a dependency graph, and runs a
    fixed-weight Graph Convolutional Network to produce a document-level
    embedding via global mean pooling.

    Requires ``spaCy``.  Install with::

        pip install 'mowen[nlp]'

    Pure Python GCN implementation — no torch_geometric required.
    """

    display_name: str = "GNN Syntactic Embeddings"
    description: str = (
        "Graph neural network embeddings from syntactic dependency "
        "graphs (requires spaCy)."
    )

    _nlp: Any = field(default=None, init=False, repr=False)
    _model_name_cache: str = field(default="", init=False, repr=False)

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="spacy_model",
                description="spaCy model for dependency parsing.",
                param_type=str,
                default="en_core_web_sm",
            ),
            ParamDef(
                name="hidden_dim",
                description="Hidden dimension of GCN layers.",
                param_type=int,
                default=64,
                min_value=8,
                max_value=512,
            ),
            ParamDef(
                name="n_layers",
                description="Number of GCN layers.",
                param_type=int,
                default=2,
                min_value=1,
                max_value=4,
            ),
            ParamDef(
                name="pooling",
                description="Global pooling method.",
                param_type=str,
                default="mean",
                choices=["mean", "max", "sum"],
            ),
            ParamDef(
                name="random_seed",
                description="Seed for GCN weight initialization.",
                param_type=int,
                default=42,
            ),
        ]

    def _ensure_nlp(self) -> None:
        model_name = self.get_param("spacy_model")
        if self._nlp is not None and self._model_name_cache == model_name:
            return

        try:
            import spacy
        except ImportError as exc:
            raise ImportError(
                "GNN embeddings require spaCy. "
                "Install with: pip install 'mowen[nlp]'"
            ) from exc

        try:
            self._nlp = spacy.load(model_name)
        except OSError as exc:
            raise ImportError(
                f"spaCy model {model_name!r} not found. "
                f"Install with: python -m spacy download {model_name}"
            ) from exc
        self._model_name_cache = model_name

    def create_event_set(self, text: str) -> NumericEventSet:
        """Parse text and return GCN-pooled embedding."""
        self._ensure_nlp()

        doc = self._nlp(text)
        if len(doc) == 0:
            hidden_dim: int = self.get_param("hidden_dim")
            return NumericEventSet([0.0] * hidden_dim)

        # Collect POS and dep label vocabularies
        pos_labels = sorted({token.pos_ for token in doc})
        dep_labels = sorted({token.dep_ for token in doc})
        pos_to_idx = {p: i for i, p in enumerate(pos_labels)}
        dep_to_idx = {d: i for i, d in enumerate(dep_labels)}

        # Build node features: token vector + POS one-hot + dep one-hot
        n_with_vec = sum(1 for t in doc if t.has_vector)
        if n_with_vec == 0:
            logger.warning(
                "No tokens have word vectors in spaCy model %r. "
                "GNN features will rely on POS/dep tags only.",
                self.get_param("spacy_model"),
            )
        elif n_with_vec < len(doc) * 0.5:
            logger.warning(
                "%d/%d tokens lack word vectors (%.0f%% OOV). "
                "GNN embedding quality may be degraded.",
                len(doc) - n_with_vec,
                len(doc),
                (len(doc) - n_with_vec) / len(doc) * 100,
            )
        vec_dim = len(doc[0].vector) if doc[0].has_vector else 0
        pos_dim = len(pos_labels)
        dep_dim = len(dep_labels)
        feat_dim = vec_dim + pos_dim + dep_dim

        node_features: list[list[float]] = []
        edges: list[tuple[int, int]] = []

        for token in doc:
            feat = []
            # Token vector
            if token.has_vector:
                feat.extend(float(v) for v in token.vector)
            # POS one-hot
            pos_oh = [0.0] * pos_dim
            pos_oh[pos_to_idx[token.pos_]] = 1.0
            feat.extend(pos_oh)
            # Dep one-hot
            dep_oh = [0.0] * dep_dim
            dep_oh[dep_to_idx[token.dep_]] = 1.0
            feat.extend(dep_oh)
            node_features.append(feat)

            # Edge: head -> token
            if token.head.i != token.i:
                edges.append((token.head.i, token.i))

        # Run GCN
        hidden_dim = self.get_param("hidden_dim")
        n_layers: int = self.get_param("n_layers")
        seed: int = self.get_param("random_seed")

        gcn = _SimpleGCN(feat_dim, hidden_dim, n_layers, seed)
        node_embeds = gcn.forward(node_features, edges)

        if not node_embeds:
            return NumericEventSet([0.0] * hidden_dim)

        # Global pooling
        pooling: str = self.get_param("pooling")
        embed_dim = len(node_embeds[0])

        if pooling == "mean":
            pooled = [
                sum(ne[d] for ne in node_embeds) / len(node_embeds)
                for d in range(embed_dim)
            ]
        elif pooling == "max":
            pooled = [max(ne[d] for ne in node_embeds) for d in range(embed_dim)]
        else:  # sum
            pooled = [sum(ne[d] for ne in node_embeds) for d in range(embed_dim)]

        return NumericEventSet(pooled)

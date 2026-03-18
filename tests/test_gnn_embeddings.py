"""Tests for the GNN syntactic embedding driver."""

import pytest

# spaCy may fail on Python 3.14+ due to pydantic v1 incompatibility
_spacy_available = False
try:
    import spacy
    spacy.load("en_core_web_sm")
    _spacy_available = True
except Exception:
    pass

_skip_spacy = pytest.mark.skipif(
    not _spacy_available,
    reason="spaCy or en_core_web_sm not available",
)


@_skip_spacy
class TestGNNEmbeddings:
    def test_registered(self):
        from mowen.event_drivers import event_driver_registry
        assert "gnn_embeddings" in event_driver_registry.names()

    def test_param_defs(self):
        from mowen.event_drivers import event_driver_registry
        driver = event_driver_registry.create("gnn_embeddings")
        param_names = {p.name for p in driver.param_defs()}
        assert "spacy_model" in param_names
        assert "hidden_dim" in param_names
        assert "n_layers" in param_names
        assert "pooling" in param_names

    def test_produces_numeric_event_set(self):
        from mowen.event_drivers import event_driver_registry
        from mowen.types import NumericEventSet

        driver = event_driver_registry.create("gnn_embeddings")
        result = driver.create_event_set(
            "The quick brown fox jumps over the lazy dog."
        )
        assert isinstance(result, NumericEventSet)
        assert len(result) == 64  # default hidden_dim

    def test_custom_hidden_dim(self):
        from mowen.event_drivers import event_driver_registry
        from mowen.types import NumericEventSet

        driver = event_driver_registry.create(
            "gnn_embeddings", {"hidden_dim": 32}
        )
        result = driver.create_event_set("Hello world.")
        assert isinstance(result, NumericEventSet)
        assert len(result) == 32

    def test_deterministic_with_seed(self):
        from mowen.event_drivers import event_driver_registry

        text = "The cat sat on the mat."
        r1 = event_driver_registry.create(
            "gnn_embeddings", {"random_seed": 42}
        ).create_event_set(text)
        r2 = event_driver_registry.create(
            "gnn_embeddings", {"random_seed": 42}
        ).create_event_set(text)
        assert list(r1) == list(r2)

    def test_different_texts_different_embeddings(self):
        from mowen.event_drivers import event_driver_registry

        driver = event_driver_registry.create("gnn_embeddings")
        r1 = driver.create_event_set("The cat sat on the mat.")
        r2 = driver.create_event_set(
            "Economic policy drives national growth."
        )
        assert list(r1) != list(r2)

    def test_empty_text(self):
        from mowen.event_drivers import event_driver_registry
        from mowen.types import NumericEventSet

        driver = event_driver_registry.create("gnn_embeddings")
        result = driver.create_event_set("")
        assert isinstance(result, NumericEventSet)
        assert len(result) == 64


def test_simple_gcn_unit():
    """Unit test the pure-Python GCN implementation."""
    from mowen.event_drivers.gnn_embeddings import _SimpleGCN

    gcn = _SimpleGCN(input_dim=3, hidden_dim=4, n_layers=2, seed=42)
    features = [[1.0, 0.0, 0.5], [0.0, 1.0, 0.5], [0.5, 0.5, 1.0]]
    edges = [(0, 1), (1, 2)]
    result = gcn.forward(features, edges)
    assert len(result) == 3
    assert len(result[0]) == 4
    # All values should be non-negative (after ReLU)
    for node in result:
        for val in node:
            assert val >= 0.0

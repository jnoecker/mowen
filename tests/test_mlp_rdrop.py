"""Tests for MLP with R-Drop regularization."""

import pytest

from mowen.analysis_methods import analysis_method_registry
from mowen.types import Document, Event, Histogram, NumericEventSet


def _make_training_data():
    return [
        (Document(text="", author="A", title="a1"),
         Histogram({Event("a"): 5, Event("b"): 1})),
        (Document(text="", author="A", title="a2"),
         Histogram({Event("a"): 4, Event("b"): 2})),
        (Document(text="", author="B", title="b1"),
         Histogram({Event("a"): 1, Event("b"): 5})),
        (Document(text="", author="B", title="b2"),
         Histogram({Event("a"): 2, Event("b"): 4})),
    ]


def _make_numeric_data():
    return [
        (Document(text="", author="A", title="a1"),
         NumericEventSet([1.0, 0.0, 0.5])),
        (Document(text="", author="A", title="a2"),
         NumericEventSet([0.9, 0.1, 0.6])),
        (Document(text="", author="B", title="b1"),
         NumericEventSet([0.0, 1.0, 0.5])),
        (Document(text="", author="B", title="b2"),
         NumericEventSet([0.1, 0.9, 0.4])),
    ]


class TestMLPRDrop:
    def test_rdrop_disabled_uses_sklearn(self):
        """Default r_drop=False should work normally."""
        pytest.importorskip("sklearn")
        method = analysis_method_registry.create(
            "mlp", {"r_drop": False, "max_iter": 100}
        )
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "A"
        assert len(results) == 2

    def test_rdrop_enabled_with_histograms(self):
        torch = pytest.importorskip("torch")
        method = analysis_method_registry.create(
            "mlp", {"r_drop": True, "max_iter": 100, "hidden_size": 16}
        )
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "A"
        assert len(results) == 2

    def test_rdrop_enabled_with_numeric(self):
        torch = pytest.importorskip("torch")
        method = analysis_method_registry.create(
            "mlp", {"r_drop": True, "max_iter": 500, "hidden_size": 16}
        )
        method.train(_make_numeric_data())
        unknown = NumericEventSet([0.85, 0.1, 0.5])
        results = method.analyze(unknown)
        assert results[0].author == "A"

    def test_rdrop_scores_are_probabilities(self):
        torch = pytest.importorskip("torch")
        method = analysis_method_registry.create(
            "mlp", {"r_drop": True, "max_iter": 50, "hidden_size": 8}
        )
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        for r in results:
            assert 0.0 <= r.score <= 1.0
        # Probabilities should sum to ~1
        total = sum(r.score for r in results)
        assert abs(total - 1.0) < 0.01

    def test_rdrop_all_authors_present(self):
        torch = pytest.importorskip("torch")
        method = analysis_method_registry.create(
            "mlp", {"r_drop": True, "max_iter": 50}
        )
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        authors = {r.author for r in results}
        assert authors == {"A", "B"}

    def test_device_param_exists(self):
        method = analysis_method_registry.create("mlp")
        param_names = {p.name for p in method.param_defs()}
        assert "device" in param_names

    def test_device_cpu_explicit(self):
        torch = pytest.importorskip("torch")
        method = analysis_method_registry.create(
            "mlp", {"r_drop": True, "max_iter": 50, "device": "cpu"}
        )
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 5, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "A"
        assert method._device == torch.device("cpu")

    def test_device_auto_resolves(self):
        torch = pytest.importorskip("torch")
        method = analysis_method_registry.create(
            "mlp", {"r_drop": True, "max_iter": 50, "device": "auto"}
        )
        method.train(_make_training_data())
        # auto should resolve to some valid device
        assert method._device is not None
        unknown = Histogram({Event("a"): 5, Event("b"): 1})
        results = method.analyze(unknown)
        assert len(results) == 2

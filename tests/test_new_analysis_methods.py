"""Tests for Phase 4 analysis methods."""

import pytest

from mowen.analysis_methods import analysis_method_registry
from mowen.types import Document, Event, Histogram


def _make_training_data():
    """Larger training set for sklearn methods."""
    data = []
    for i, (a, b) in enumerate([(5, 1), (4, 2), (6, 1), (5, 2)]):
        data.append((Document(text="", author="Author A", title=f"a{i}"),
                      Histogram({Event("a"): a, Event("b"): b})))
    for i, (a, b) in enumerate([(1, 5), (2, 4), (1, 6), (2, 5)]):
        data.append((Document(text="", author="Author B", title=f"b{i}"),
                      Histogram({Event("a"): a, Event("b"): b})))
    return data


class TestRandomForest:
    def test_attributes_correctly(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("random_forest", {"n_estimators": 10})
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("random_forest", {"n_estimators": 10})
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        assert {r.author for r in results} == {"Author A", "Author B"}

    def test_scores_are_probabilities(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("random_forest", {"n_estimators": 10})
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert all(0 <= r.score <= 1 for r in results)
        assert results[0].score >= results[-1].score


class TestLogisticRegression:
    def test_attributes_correctly(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("logistic_regression")
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("logistic_regression")
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        assert {r.author for r in results} == {"Author A", "Author B"}

    def test_scores_are_probabilities(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("logistic_regression")
        method.train(_make_training_data())
        results = method.analyze(Histogram({Event("a"): 6, Event("b"): 1}))
        assert all(0 <= r.score <= 1 for r in results)


class TestMultilayerPerceptron:
    def test_attributes_correctly(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("mlp", {"hidden_size": 10, "max_iter": 500})
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("mlp", {"hidden_size": 10, "max_iter": 500})
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        assert {r.author for r in results} == {"Author A", "Author B"}

    def test_scores_are_probabilities(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("mlp", {"hidden_size": 10, "max_iter": 500})
        method.train(_make_training_data())
        results = method.analyze(Histogram({Event("a"): 6, Event("b"): 1}))
        assert all(0 <= r.score <= 1 for r in results)
        assert results[0].score >= results[-1].score

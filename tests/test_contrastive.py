"""Tests for the contrastive learning analysis method."""

import pytest

from mowen.analysis_methods import analysis_method_registry
from mowen.types import Document, Event, Histogram, NumericEventSet


def _make_numeric_training_data():
    """Create training data with NumericEventSet inputs."""
    return [
        (
            Document(text="", author="A", title="a1"),
            NumericEventSet([1.0, 0.0, 0.5, 0.2]),
        ),
        (
            Document(text="", author="A", title="a2"),
            NumericEventSet([0.9, 0.1, 0.6, 0.1]),
        ),
        (
            Document(text="", author="A", title="a3"),
            NumericEventSet([0.8, 0.05, 0.55, 0.15]),
        ),
        (
            Document(text="", author="B", title="b1"),
            NumericEventSet([0.0, 1.0, 0.5, 0.8]),
        ),
        (
            Document(text="", author="B", title="b2"),
            NumericEventSet([0.1, 0.9, 0.4, 0.9]),
        ),
        (
            Document(text="", author="B", title="b3"),
            NumericEventSet([0.05, 0.95, 0.45, 0.85]),
        ),
    ]


class TestContrastive:
    def test_registered(self):
        assert "contrastive" in analysis_method_registry.names()

    def test_correct_author_ranked_first(self):
        method = analysis_method_registry.create("contrastive")
        method.train(_make_numeric_training_data())

        unknown = NumericEventSet([0.85, 0.1, 0.5, 0.2])
        results = method.analyze(unknown)
        assert results[0].author == "A"

    def test_all_authors_present(self):
        method = analysis_method_registry.create("contrastive")
        method.train(_make_numeric_training_data())

        unknown = NumericEventSet([0.5, 0.5, 0.5, 0.5])
        results = method.analyze(unknown)
        authors = {r.author for r in results}
        assert authors == {"A", "B"}

    def test_scores_sorted_descending(self):
        method = analysis_method_registry.create("contrastive")
        method.train(_make_numeric_training_data())

        unknown = NumericEventSet([0.5, 0.5, 0.5, 0.5])
        results = method.analyze(unknown)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_lower_is_better_false(self):
        method = analysis_method_registry.create("contrastive")
        assert method.lower_is_better is False

    def test_with_projection(self):
        """Projection should still produce correct attributions."""
        numpy = pytest.importorskip("numpy")
        method = analysis_method_registry.create(
            "contrastive",
            {"projection_dim": 2, "n_epochs": 20, "random_seed": 42},
        )
        method.train(_make_numeric_training_data())

        unknown = NumericEventSet([0.85, 0.1, 0.5, 0.2])
        results = method.analyze(unknown)
        assert results[0].author == "A"
        assert len(results) == 2

    def test_deterministic_with_seed(self):
        numpy = pytest.importorskip("numpy")
        results_list = []
        for _ in range(2):
            method = analysis_method_registry.create(
                "contrastive",
                {"projection_dim": 2, "n_epochs": 10, "random_seed": 42},
            )
            method.train(_make_numeric_training_data())
            results_list.append(method.analyze(NumericEventSet([0.5, 0.5, 0.5, 0.5])))

        for r1, r2 in zip(results_list[0], results_list[1]):
            assert r1.author == r2.author
            assert r1.score == pytest.approx(r2.score)

    def test_with_histograms(self):
        """Should work with discrete Histogram inputs (shared vocab)."""
        data = [
            (
                Document(text="", author="A", title="a1"),
                Histogram({Event("x"): 5, Event("y"): 1}),
            ),
            (
                Document(text="", author="A", title="a2"),
                Histogram({Event("x"): 4, Event("y"): 2}),
            ),
            (
                Document(text="", author="B", title="b1"),
                Histogram({Event("x"): 1, Event("y"): 5}),
            ),
            (
                Document(text="", author="B", title="b2"),
                Histogram({Event("x"): 2, Event("y"): 4}),
            ),
        ]
        method = analysis_method_registry.create("contrastive")
        method.train(data)
        unknown = Histogram({Event("x"): 6, Event("y"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "A"
        assert len(results) == 2

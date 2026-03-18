"""Tests for analysis method implementations."""

import pytest

from mowen.analysis_methods import analysis_method_registry
from mowen.distance_functions import distance_function_registry
from mowen.types import Document, Event, Histogram


def _make_training_data():
    """Create simple training data with two authors."""
    doc_a1 = Document(text="", author="Author A", title="a1")
    hist_a1 = Histogram({Event("a"): 5, Event("b"): 1})

    doc_a2 = Document(text="", author="Author A", title="a2")
    hist_a2 = Histogram({Event("a"): 4, Event("b"): 2})

    doc_b1 = Document(text="", author="Author B", title="b1")
    hist_b1 = Histogram({Event("a"): 1, Event("b"): 5})

    doc_b2 = Document(text="", author="Author B", title="b2")
    hist_b2 = Histogram({Event("a"): 2, Event("b"): 4})

    return [(doc_a1, hist_a1), (doc_a2, hist_a2), (doc_b1, hist_b1), (doc_b2, hist_b2)]


class TestNearestNeighbor:
    def test_attributes_to_closer_author(self):
        method = analysis_method_registry.create("nearest_neighbor")
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())

        # Unknown is similar to Author A
        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"
        assert len(results) == 2

    def test_all_authors_present(self):
        method = analysis_method_registry.create("nearest_neighbor")
        method.distance_function = distance_function_registry.create("manhattan")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        authors = {r.author for r in results}
        assert authors == {"Author A", "Author B"}

    def test_scores_are_distances(self):
        method = analysis_method_registry.create("nearest_neighbor")
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        # Scores should be non-negative distances, sorted ascending
        assert all(r.score >= 0 for r in results)
        assert results[0].score <= results[-1].score


class TestKNN:
    def test_majority_vote(self):
        method = analysis_method_registry.create("knn", {"k": 3})
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())

        # Unknown is very similar to Author A
        unknown = Histogram({Event("a"): 10, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_k_larger_than_corpus(self):
        method = analysis_method_registry.create("knn", {"k": 100})
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 5, Event("b"): 1})
        results = method.analyze(unknown)
        # Should still work — uses all available documents
        assert len(results) > 0

    def test_scores_are_proportions(self):
        method = analysis_method_registry.create("knn", {"k": 4})
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        total = sum(r.score for r in results)
        assert abs(total - 1.0) < 1e-9


class TestCentroid:
    def test_attributes_to_closer_author(self):
        method = analysis_method_registry.create("centroid")
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        method = analysis_method_registry.create("centroid")
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        authors = {r.author for r in results}
        assert authors == {"Author A", "Author B"}

    def test_scores_non_negative_and_sorted(self):
        method = analysis_method_registry.create("centroid")
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert all(r.score >= 0 for r in results)
        assert results[0].score <= results[-1].score


class TestAbsoluteCentroid:
    def test_attributes_to_closer_author(self):
        method = analysis_method_registry.create("absolute_centroid")
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        method = analysis_method_registry.create("absolute_centroid")
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        authors = {r.author for r in results}
        assert authors == {"Author A", "Author B"}

    def test_scores_non_negative_and_sorted(self):
        method = analysis_method_registry.create("absolute_centroid")
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert all(r.score >= 0 for r in results)
        assert results[0].score <= results[-1].score


class TestBurrowsDelta:
    def test_attributes_to_closer_author(self):
        method = analysis_method_registry.create("burrows_delta")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        method = analysis_method_registry.create("burrows_delta")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        authors = {r.author for r in results}
        assert authors == {"Author A", "Author B"}

    def test_scores_non_negative_and_sorted(self):
        method = analysis_method_registry.create("burrows_delta")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert all(r.score >= 0 for r in results)
        assert results[0].score <= results[-1].score


def _make_larger_training_data():
    """Larger training set for sklearn methods that need more samples."""
    data = []
    for i, (a_count, b_count) in enumerate([(5, 1), (4, 2), (6, 1), (5, 2)]):
        doc = Document(text="", author="Author A", title=f"a{i}")
        data.append((doc, Histogram({Event("a"): a_count, Event("b"): b_count})))
    for i, (a_count, b_count) in enumerate([(1, 5), (2, 4), (1, 6), (2, 5)]):
        doc = Document(text="", author="Author B", title=f"b{i}")
        data.append((doc, Histogram({Event("a"): a_count, Event("b"): b_count})))
    return data


class TestSVM:
    def test_attributes_to_closer_author(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("svm")
        method.train(_make_larger_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("svm")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        authors = {r.author for r in results}
        assert authors == {"Author A", "Author B"}

    def test_scores_are_probabilities(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("svm")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert all(0 <= r.score <= 1 for r in results)
        assert results[0].score >= results[-1].score


class TestDecisionTree:
    def test_attributes_to_closer_author(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("decision_tree")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("decision_tree")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        authors = {r.author for r in results}
        assert authors == {"Author A", "Author B"}

    def test_scores_are_probabilities(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("decision_tree")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert all(0 <= r.score <= 1 for r in results)
        assert results[0].score >= results[-1].score


class TestLDA:
    def test_attributes_to_closer_author(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("lda")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("lda")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        authors = {r.author for r in results}
        assert authors == {"Author A", "Author B"}

    def test_scores_are_probabilities(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("lda")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert all(0 <= r.score <= 1 for r in results)
        assert results[0].score >= results[-1].score


class TestMarkovChain:
    def test_attributes_to_closer_author(self):
        method = analysis_method_registry.create("markov_chain")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        method = analysis_method_registry.create("markov_chain")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        authors = {r.author for r in results}
        assert authors == {"Author A", "Author B"}

    def test_scores_sorted_descending(self):
        method = analysis_method_registry.create("markov_chain")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        # Log-likelihoods: higher = better, sorted descending
        assert results[0].score >= results[-1].score


class TestNaiveBayes:
    def test_attributes_to_closer_author(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("naive_bayes")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("naive_bayes")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        authors = {r.author for r in results}
        assert authors == {"Author A", "Author B"}

    def test_scores_are_probabilities(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("naive_bayes")
        method.train(_make_training_data())

        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert all(0 <= r.score <= 1 for r in results)
        assert results[0].score >= results[-1].score


def _make_large_training_data():
    """Larger training set for sklearn methods."""
    data = []
    for i, (a, b) in enumerate([(5, 1), (4, 2), (6, 1), (5, 2)]):
        data.append(
            (
                Document(text="", author="Author A", title=f"a{i}"),
                Histogram({Event("a"): a, Event("b"): b}),
            )
        )
    for i, (a, b) in enumerate([(1, 5), (2, 4), (1, 6), (2, 5)]):
        data.append(
            (
                Document(text="", author="Author B", title=f"b{i}"),
                Histogram({Event("a"): a, Event("b"): b}),
            )
        )
    return data


class TestRandomForest:
    def test_attributes_correctly(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("random_forest", {"n_estimators": 10})
        method.train(_make_large_training_data())
        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("random_forest", {"n_estimators": 10})
        method.train(_make_large_training_data())
        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        assert {r.author for r in results} == {"Author A", "Author B"}

    def test_scores_are_probabilities(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("random_forest", {"n_estimators": 10})
        method.train(_make_large_training_data())
        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert all(0 <= r.score <= 1 for r in results)
        assert results[0].score >= results[-1].score


class TestLogisticRegression:
    def test_attributes_correctly(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("logistic_regression")
        method.train(_make_large_training_data())
        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("logistic_regression")
        method.train(_make_large_training_data())
        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        assert {r.author for r in results} == {"Author A", "Author B"}

    def test_scores_are_probabilities(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create("logistic_regression")
        method.train(_make_large_training_data())
        results = method.analyze(Histogram({Event("a"): 6, Event("b"): 1}))
        assert all(0 <= r.score <= 1 for r in results)


class TestMultilayerPerceptron:
    def test_attributes_correctly(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create(
            "mlp", {"hidden_size": 10, "max_iter": 500}
        )
        method.train(_make_large_training_data())
        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "Author A"

    def test_all_authors_present(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create(
            "mlp", {"hidden_size": 10, "max_iter": 500}
        )
        method.train(_make_large_training_data())
        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        assert {r.author for r in results} == {"Author A", "Author B"}

    def test_scores_are_probabilities(self):
        sklearn = pytest.importorskip("sklearn")
        method = analysis_method_registry.create(
            "mlp", {"hidden_size": 10, "max_iter": 500}
        )
        method.train(_make_large_training_data())
        results = method.analyze(Histogram({Event("a"): 6, Event("b"): 1}))
        assert all(0 <= r.score <= 1 for r in results)
        assert results[0].score >= results[-1].score

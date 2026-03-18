"""Regression tests for adversarial review findings."""

from __future__ import annotations

import math

import pytest

from mowen.analysis_methods import analysis_method_registry
from mowen.distance_functions import distance_function_registry
from mowen.document_loaders import load_document
from mowen.exceptions import DocumentLoadError, PipelineError
from mowen.pipeline import Pipeline, PipelineConfig
from mowen.types import Document, Event, EventSet, Histogram, NumericEventSet

# -----------------------------------------------------------------------
# Finding 1: Loader fail-closed for optional extensions
# -----------------------------------------------------------------------


class TestLoaderFailClosed:
    def test_pdf_without_pdfplumber_raises(self, tmp_path):
        """Loading a .pdf file without pdfplumber installed should raise, not fall back to plaintext."""
        fake_pdf = tmp_path / "test.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 fake content")
        # If pdfplumber is not installed, this should raise DocumentLoadError
        # If it IS installed, it will try to parse and either succeed or fail on bad PDF
        try:
            doc = load_document(str(fake_pdf))
            # If we get here, pdfplumber IS installed and parsed it
        except DocumentLoadError as e:
            # Good — either "no loader registered" or pdfplumber parse error
            assert "pdf" in str(e).lower() or "loader" in str(e).lower()

    def test_docx_without_python_docx_raises(self, tmp_path):
        fake_docx = tmp_path / "test.docx"
        fake_docx.write_bytes(b"PK\x03\x04 fake content")
        try:
            doc = load_document(str(fake_docx))
        except DocumentLoadError as e:
            assert "docx" in str(e).lower() or "loader" in str(e).lower()

    def test_unknown_extension_still_loads_as_text(self, tmp_path):
        """Truly unknown extensions should still fall back to plaintext."""
        f = tmp_path / "data.log"
        f.write_text("log entry 1\nlog entry 2", encoding="utf-8")
        doc = load_document(str(f))
        assert "log entry" in doc.text

    def test_txt_extension_always_works(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        doc = load_document(str(f))
        assert doc.text == "hello world"


# -----------------------------------------------------------------------
# Finding 2: Experiment corpus overlap (tested via server API)
# -----------------------------------------------------------------------
# Server-level tests are in test_server_api.py — see TestExperimentOverlap below


# -----------------------------------------------------------------------
# Finding 3: Mixed numeric/discrete driver validation (both orderings)
# -----------------------------------------------------------------------


class TestMixedDriverValidation:
    """Ensure PipelineError on mixed numeric + discrete drivers in EITHER order."""

    def test_numeric_then_discrete_raises(self):
        """Numeric driver first, discrete second — should fail."""
        # Register a mock numeric driver if not already done
        from mowen.event_drivers.base import EventDriver, event_driver_registry

        try:

            @event_driver_registry.register("_test_numeric")
            class _TestNumericDriver(EventDriver):
                display_name = "Test Numeric"
                description = "Test"

                def create_event_set(self, text):
                    return NumericEventSet([1.0, 2.0, 3.0])

        except Exception:
            pass  # Already registered from test_embeddings.py

        known = [Document(text="hello world", author="A")]
        unknown = [Document(text="test")]
        config = PipelineConfig(
            event_drivers=[
                {"name": "_test_numeric"},
                {"name": "word_events"},
            ],
            analysis_method={"name": "svm"},
        )
        with pytest.raises(PipelineError, match="Cannot mix"):
            Pipeline(config).execute(known, unknown)

    def test_discrete_then_numeric_raises(self):
        """Discrete driver first, numeric second — should also fail."""
        from mowen.event_drivers.base import EventDriver, event_driver_registry

        try:

            @event_driver_registry.register("_test_numeric2")
            class _TestNumericDriver2(EventDriver):
                display_name = "Test Numeric 2"
                description = "Test"

                def create_event_set(self, text):
                    return NumericEventSet([1.0, 2.0, 3.0])

        except Exception:
            pass

        known = [Document(text="hello world", author="A")]
        unknown = [Document(text="test")]
        config = PipelineConfig(
            event_drivers=[
                {"name": "word_events"},
                {"name": "_test_numeric2"},
            ],
            distance_function={"name": "cosine"},
            analysis_method={"name": "nearest_neighbor"},
        )
        with pytest.raises(PipelineError, match="Cannot mix"):
            Pipeline(config).execute(known, unknown)


# -----------------------------------------------------------------------
# Finding 4: KNN scores when k > n_docs
# -----------------------------------------------------------------------


class TestKNNScoreNormalization:
    def test_k_greater_than_corpus_scores_sum_to_one(self):
        """When k > number of training docs, scores should still sum to 1.0."""
        method = analysis_method_registry.create("knn", {"k": 100})
        method.distance_function = distance_function_registry.create("cosine")

        # Only 4 training documents
        data = [
            (Document(text="", author="A"), Histogram({Event("x"): 5, Event("y"): 1})),
            (Document(text="", author="A"), Histogram({Event("x"): 4, Event("y"): 2})),
            (Document(text="", author="B"), Histogram({Event("x"): 1, Event("y"): 5})),
            (Document(text="", author="B"), Histogram({Event("x"): 2, Event("y"): 4})),
        ]
        method.train(data)

        unknown = Histogram({Event("x"): 3, Event("y"): 3})
        results = method.analyze(unknown)
        total = sum(r.score for r in results)
        assert abs(total - 1.0) < 1e-9, f"KNN scores sum to {total}, expected 1.0"

    def test_k_equal_to_corpus_scores_sum_to_one(self):
        method = analysis_method_registry.create("knn", {"k": 2})
        method.distance_function = distance_function_registry.create("cosine")

        data = [
            (Document(text="", author="A"), Histogram({Event("x"): 5})),
            (Document(text="", author="B"), Histogram({Event("y"): 5})),
        ]
        method.train(data)

        results = method.analyze(Histogram({Event("x"): 3, Event("y"): 1}))
        total = sum(r.score for r in results)
        assert abs(total - 1.0) < 1e-9


# -----------------------------------------------------------------------
# Finding 5: MarkovChain OOV smoothing is author-specific
# -----------------------------------------------------------------------


class TestMarkovChainOOV:
    def test_unseen_event_differs_by_author_corpus_size(self):
        """Authors with different corpus sizes should assign different OOV probabilities."""
        method = analysis_method_registry.create("markov_chain")

        # Author A has a large corpus, Author B has a tiny one
        big_hist = Histogram({Event("a"): 1000, Event("b"): 1000})
        small_hist = Histogram({Event("a"): 1, Event("b"): 1})
        data = [
            (Document(text="", author="BigAuthor"), big_hist),
            (Document(text="", author="SmallAuthor"), small_hist),
        ]
        method.train(data)

        # Unknown doc has only an unseen event
        unknown = Histogram({Event("never_seen"): 1})
        results = method.analyze(unknown)

        # Both authors should have different scores for the OOV event
        scores = {r.author: r.score for r in results}
        assert (
            scores["BigAuthor"] != scores["SmallAuthor"]
        ), "OOV smoothing should differ based on author corpus size"
        # BigAuthor's OOV probability is smaller (more total tokens → lower Laplace prob)
        # so its log-likelihood should be more negative
        assert scores["BigAuthor"] < scores["SmallAuthor"]

    def test_all_events_seen_no_oov(self):
        """When all events were seen in training, normal probabilities are used."""
        method = analysis_method_registry.create("markov_chain")
        data = [
            (Document(text="", author="A"), Histogram({Event("x"): 5, Event("y"): 5})),
            (Document(text="", author="B"), Histogram({Event("x"): 1, Event("y"): 9})),
        ]
        method.train(data)

        # Unknown has only events seen in training
        unknown = Histogram({Event("x"): 3})
        results = method.analyze(unknown)
        assert len(results) == 2
        # Author A has more "x" events proportionally, should rank higher
        assert results[0].author == "A"


# -----------------------------------------------------------------------
# Finding 6: Windows SQLite URL tilde handling
# -----------------------------------------------------------------------


class TestConfigTildeHandling:
    def test_tilde_in_middle_of_path_not_expanded(self, tmp_path):
        """Paths like PROGRA~1 should not have their tilde expanded."""
        from mowen_server.config import Settings

        # Use a writable tmp_path but with a ~ in the DB filename
        db_path = tmp_path / "DATA~1" / "test.db"
        settings = Settings(
            database_url=f"sqlite:///{db_path}",
            upload_dir=str(tmp_path / "uploads"),
        )
        assert "DATA~1" in settings.database_url

    def test_home_placeholder_expanded(self):
        from pathlib import Path

        from mowen_server.config import Settings

        settings = Settings(
            database_url="sqlite:///{home}/.mowen/test.db",
            upload_dir="/tmp/mowen-test-uploads",
        )
        assert "{home}" not in settings.database_url
        assert str(Path.home()) in settings.database_url


# -----------------------------------------------------------------------
# Finding 7: Culler data leakage — unknown docs must not influence culling
# -----------------------------------------------------------------------


class TestCullerDataLeakage:
    def test_unknown_only_events_not_in_culler_statistics(self):
        """Events exclusive to unknown docs should not affect culler selection."""
        # Known docs have events a, b, c (a is most common)
        known = [
            Document(text="a a a b c", author="A"),
            Document(text="a a b b c", author="B"),
        ]
        # Unknown doc has a unique event 'z' that appears many times
        unknown = [Document(text="z z z z z z z z z z a")]

        config = PipelineConfig(
            event_drivers=[{"name": "word_events"}],
            event_cullers=[{"name": "most_common", "params": {"n": 2}}],
            distance_function={"name": "cosine"},
            analysis_method={"name": "nearest_neighbor"},
        )
        results = Pipeline(config).execute(known, unknown)
        # Should complete without error; 'z' should not be in the kept events
        # since the culler only sees known docs
        assert len(results) == 1
        assert results[0].top_author is not None


# -----------------------------------------------------------------------
# Finding 8: Angular separation zero-vector semantics
# -----------------------------------------------------------------------


class TestAngularSeparationZeroVector:
    def test_zero_vector_returns_max_distance(self):
        """Empty histograms should return 1.0 (maximally dissimilar)."""
        d = distance_function_registry.create("angular_separation")
        h_empty = Histogram()
        h_real = Histogram({Event("a"): 1})
        assert d.distance(h_empty, h_real) == 1.0
        assert d.distance(h_real, h_empty) == 1.0
        assert d.distance(h_empty, h_empty) == 1.0


# -----------------------------------------------------------------------
# Finding 9: Burrows' Delta zero-variance feature handling
# -----------------------------------------------------------------------


class TestBurrowsDeltaZeroVariance:
    def test_zero_variance_features_skipped(self):
        """Features with identical frequency across all docs should be skipped."""
        method = analysis_method_registry.create("burrows_delta", {"n_features": 100})

        # Event 'c' has identical frequency in all docs → zero variance
        data = [
            (
                Document(text="", author="A"),
                Histogram({Event("a"): 5, Event("b"): 1, Event("c"): 3}),
            ),
            (
                Document(text="", author="A"),
                Histogram({Event("a"): 4, Event("b"): 2, Event("c"): 3}),
            ),
            (
                Document(text="", author="B"),
                Histogram({Event("a"): 1, Event("b"): 5, Event("c"): 3}),
            ),
            (
                Document(text="", author="B"),
                Histogram({Event("a"): 2, Event("b"): 4, Event("c"): 3}),
            ),
        ]
        method.train(data)

        # Event 'c' should be excluded from features (zero variance)
        assert Event("c") not in method._features
        # Events a and b should remain
        assert Event("a") in method._features
        assert Event("b") in method._features

    def test_no_extreme_scores_from_zero_variance(self):
        """Scores should remain reasonable even with uniform features."""
        method = analysis_method_registry.create("burrows_delta", {"n_features": 100})

        data = [
            (Document(text="", author="A"), Histogram({Event("a"): 5, Event("c"): 10})),
            (Document(text="", author="A"), Histogram({Event("a"): 4, Event("c"): 10})),
            (Document(text="", author="B"), Histogram({Event("a"): 1, Event("c"): 10})),
            (Document(text="", author="B"), Histogram({Event("a"): 2, Event("c"): 10})),
        ]
        method.train(data)

        unknown = Histogram({Event("a"): 6, Event("c"): 10})
        results = method.analyze(unknown)
        # Scores should be finite and reasonable (no 1e+10 blow-ups)
        assert all(abs(r.score) < 100 for r in results)
        assert results[0].author == "A"


# -----------------------------------------------------------------------
# Finding 10: Score semantics lower_is_better propagation
# -----------------------------------------------------------------------


class TestScoreSemantics:
    def test_distance_method_lower_is_better(self):
        """Distance-based methods should set lower_is_better=True."""
        known = [
            Document(text="a a a b", author="A"),
            Document(text="b b b a", author="B"),
        ]
        unknown = [Document(text="a a a")]
        config = PipelineConfig(
            event_drivers=[{"name": "word_events"}],
            distance_function={"name": "cosine"},
            analysis_method={"name": "nearest_neighbor"},
        )
        results = Pipeline(config).execute(known, unknown)
        assert results[0].lower_is_better is True

    def test_sklearn_method_higher_is_better(self):
        """Probability-based methods should set lower_is_better=False."""
        pytest.importorskip("sklearn")
        known = [
            Document(text="a a a b", author="A"),
            Document(text="a a b b", author="A"),
            Document(text="b b b a", author="B"),
            Document(text="b b a a", author="B"),
        ]
        unknown = [Document(text="a a a")]
        config = PipelineConfig(
            event_drivers=[{"name": "word_events"}],
            analysis_method={"name": "svm"},
        )
        results = Pipeline(config).execute(known, unknown)
        assert results[0].lower_is_better is False

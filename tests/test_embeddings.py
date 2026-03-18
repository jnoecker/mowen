"""Tests for the numeric/embedding pipeline path.

These tests use mock embeddings (no actual transformer model required)
to verify the pipeline correctly handles NumericEventSet objects.
"""

from __future__ import annotations

import math

import pytest

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.exceptions import PipelineError
from mowen.pipeline import Pipeline, PipelineConfig
from mowen.registry import Registry
from mowen.types import Document, EventSet, NumericEventSet

# -- Mock embedding driver (no HuggingFace needed) --------------------------

# Use a separate registry so we don't pollute the real one
_test_registry: Registry[EventDriver] = Registry("test_event_driver")


class MockEmbeddingDriver(EventDriver):
    """Produces fake embeddings based on simple text statistics."""

    display_name = "Mock Embeddings"
    description = "Test-only mock embedding driver"

    def create_event_set(self, text: str) -> EventSet:
        words = text.lower().split()
        n_words = len(words)
        avg_word_len = sum(len(w) for w in words) / max(n_words, 1)
        unique_ratio = len(set(words)) / max(n_words, 1)
        punct_ratio = sum(1 for c in text if c in ".,;:!?") / max(len(text), 1)
        upper_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        return NumericEventSet([n_words, avg_word_len, unique_ratio, punct_ratio, upper_ratio])  # type: ignore[return-value]


# Register in the real registry for pipeline tests
# We need to handle the case where it might already be registered
try:
    event_driver_registry.register("mock_embeddings")(MockEmbeddingDriver)
except Exception:
    pass


class TestNumericEventSet:
    def test_is_list_of_floats(self):
        nes = NumericEventSet([1.0, 2.0, 3.0])
        assert len(nes) == 3
        assert nes[0] == 1.0

    def test_extends(self):
        nes = NumericEventSet([1.0, 2.0])
        nes.extend([3.0, 4.0])
        assert len(nes) == 4

    def test_isinstance_check(self):
        nes = NumericEventSet([1.0])
        assert isinstance(nes, NumericEventSet)
        assert isinstance(nes, list)
        # NumericEventSet is NOT an EventSet
        assert not isinstance(nes, EventSet)


class TestNumericPipeline:
    """Test the pipeline with mock embedding drivers."""

    @pytest.fixture
    def known_docs(self):
        return [
            Document(
                text="The government must protect liberty through strong federal power. "
                "The union requires effective governance and taxation authority.",
                author="Hamilton",
            ),
            Document(
                text="The government needs a strong military and a central bank. "
                "Federal authority must extend to commerce and defense.",
                author="Hamilton",
            ),
            Document(
                text="Separate the powers into branches. Factions are best "
                "controlled in a large republic with diverse interests.",
                author="Madison",
            ),
            Document(
                text="The rights of individuals must be protected by a bill "
                "of rights. Tyranny comes from concentrated power.",
                author="Madison",
            ),
        ]

    @pytest.fixture
    def unknown_docs(self):
        return [
            Document(
                text="A strong federal government is essential for national "
                "defense and the protection of individual liberties.",
            )
        ]

    def test_embedding_pipeline_with_svm(self, known_docs, unknown_docs):
        sklearn = pytest.importorskip("sklearn")
        config = PipelineConfig(
            canonicizers=[{"name": "unify_case"}],
            event_drivers=[{"name": "mock_embeddings"}],
            analysis_method={"name": "svm"},
        )
        results = Pipeline(config).execute(known_docs, unknown_docs)
        assert len(results) == 1
        assert len(results[0].rankings) == 2
        authors = {r.author for r in results[0].rankings}
        assert authors == {"Hamilton", "Madison"}
        # Scores should be valid probabilities
        assert all(0 <= r.score <= 1 for r in results[0].rankings)

    def test_embedding_pipeline_with_naive_bayes(self, known_docs, unknown_docs):
        sklearn = pytest.importorskip("sklearn")
        config = PipelineConfig(
            event_drivers=[{"name": "mock_embeddings"}],
            analysis_method={"name": "naive_bayes"},
        )
        results = Pipeline(config).execute(known_docs, unknown_docs)
        assert len(results) == 1
        assert len(results[0].rankings) == 2

    def test_embedding_pipeline_with_decision_tree(self, known_docs, unknown_docs):
        sklearn = pytest.importorskip("sklearn")
        config = PipelineConfig(
            event_drivers=[{"name": "mock_embeddings"}],
            analysis_method={"name": "decision_tree"},
        )
        results = Pipeline(config).execute(known_docs, unknown_docs)
        assert len(results) == 1

    def test_embedding_pipeline_with_lda(self, known_docs, unknown_docs):
        sklearn = pytest.importorskip("sklearn")
        config = PipelineConfig(
            event_drivers=[{"name": "mock_embeddings"}],
            analysis_method={"name": "lda"},
        )
        results = Pipeline(config).execute(known_docs, unknown_docs)
        assert len(results) == 1

    def test_embedding_pipeline_no_distance_needed(self, known_docs, unknown_docs):
        """Numeric path should work without a distance function."""
        sklearn = pytest.importorskip("sklearn")
        config = PipelineConfig(
            event_drivers=[{"name": "mock_embeddings"}],
            # No distance_function — should be fine for sklearn methods
            analysis_method={"name": "svm"},
        )
        results = Pipeline(config).execute(known_docs, unknown_docs)
        assert len(results) == 1

    def test_embedding_pipeline_cullers_skipped(self, known_docs, unknown_docs):
        """Event cullers should be ignored in the numeric path."""
        sklearn = pytest.importorskip("sklearn")
        config = PipelineConfig(
            event_drivers=[{"name": "mock_embeddings"}],
            event_cullers=[{"name": "most_common", "params": {"n": 10}}],
            analysis_method={"name": "svm"},
        )
        # Should not raise — cullers are simply skipped
        results = Pipeline(config).execute(known_docs, unknown_docs)
        assert len(results) == 1

    def test_cannot_mix_numeric_and_discrete(self, known_docs, unknown_docs):
        """Mixing embedding drivers with discrete drivers should fail."""
        config = PipelineConfig(
            event_drivers=[
                {"name": "word_events"},
                {"name": "mock_embeddings"},
            ],
            distance_function={"name": "cosine"},
            analysis_method={"name": "nearest_neighbor"},
        )
        with pytest.raises(PipelineError, match="Cannot mix"):
            Pipeline(config).execute(known_docs, unknown_docs)

    def test_embedding_with_canonicizers(self, known_docs, unknown_docs):
        """Canonicizers should still work in the numeric path."""
        sklearn = pytest.importorskip("sklearn")
        config = PipelineConfig(
            canonicizers=[{"name": "unify_case"}, {"name": "normalize_whitespace"}],
            event_drivers=[{"name": "mock_embeddings"}],
            analysis_method={"name": "svm"},
        )
        results = Pipeline(config).execute(known_docs, unknown_docs)
        assert len(results) == 1

    def test_multiple_unknown_docs(self, known_docs):
        """Multiple unknown documents should each get results."""
        sklearn = pytest.importorskip("sklearn")
        unknowns = [
            Document(text="The government must be strong and effective."),
            Document(text="Factions threaten liberty in small republics."),
        ]
        config = PipelineConfig(
            event_drivers=[{"name": "mock_embeddings"}],
            analysis_method={"name": "svm"},
        )
        results = Pipeline(config).execute(known_docs, unknowns)
        assert len(results) == 2
        assert results[0].unknown_document is unknowns[0]
        assert results[1].unknown_document is unknowns[1]

    def test_progress_callback_in_numeric_mode(self, known_docs, unknown_docs):
        sklearn = pytest.importorskip("sklearn")
        progress_log: list[tuple[float, str]] = []

        config = PipelineConfig(
            event_drivers=[{"name": "mock_embeddings"}],
            analysis_method={"name": "svm"},
        )
        Pipeline(
            config, progress_callback=lambda f, m: progress_log.append((f, m))
        ).execute(known_docs, unknown_docs)
        assert len(progress_log) > 0
        assert progress_log[-1][0] >= 0.9

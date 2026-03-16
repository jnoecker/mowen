"""Tests for the pipeline orchestrator."""

import pytest

from mowen.exceptions import PipelineError
from mowen.pipeline import Pipeline, PipelineConfig
from mowen.types import Document


class TestPipelineConfig:
    def test_default_config(self):
        config = PipelineConfig()
        assert config.canonicizers == []
        assert config.event_drivers == []
        assert config.event_cullers == []


class TestPipeline:
    def test_full_pipeline(self, sample_documents, unknown_document):
        config = PipelineConfig(
            canonicizers=[{"name": "unify_case"}],
            event_drivers=[{"name": "character_ngram", "params": {"n": 3}}],
            distance_function={"name": "cosine"},
            analysis_method={"name": "nearest_neighbor"},
        )
        results = Pipeline(config).execute(sample_documents, [unknown_document])
        assert len(results) == 1
        assert results[0].top_author is not None
        assert len(results[0].rankings) == 2  # two distinct authors

    def test_pipeline_with_culler(self, sample_documents, unknown_document):
        config = PipelineConfig(
            event_drivers=[{"name": "word_events"}],
            event_cullers=[{"name": "most_common", "params": {"n": 10}}],
            distance_function={"name": "manhattan"},
            analysis_method={"name": "knn", "params": {"k": 3}},
        )
        results = Pipeline(config).execute(sample_documents, [unknown_document])
        assert len(results) == 1
        assert results[0].top_author is not None

    def test_pipeline_with_multiple_canonicizers(self, sample_documents, unknown_document):
        config = PipelineConfig(
            canonicizers=[
                {"name": "unify_case"},
                {"name": "normalize_whitespace"},
                {"name": "strip_punctuation"},
            ],
            event_drivers=[{"name": "character_ngram", "params": {"n": 2}}],
            distance_function={"name": "cosine"},
            analysis_method={"name": "nearest_neighbor"},
        )
        results = Pipeline(config).execute(sample_documents, [unknown_document])
        assert len(results) == 1

    def test_no_known_documents(self, unknown_document):
        config = PipelineConfig(
            event_drivers=[{"name": "word_events"}],
            distance_function={"name": "cosine"},
            analysis_method={"name": "nearest_neighbor"},
        )
        with pytest.raises(PipelineError, match="known document"):
            Pipeline(config).execute([], [unknown_document])

    def test_no_unknown_documents(self, sample_documents):
        config = PipelineConfig(
            event_drivers=[{"name": "word_events"}],
            distance_function={"name": "cosine"},
            analysis_method={"name": "nearest_neighbor"},
        )
        with pytest.raises(PipelineError, match="unknown document"):
            Pipeline(config).execute(sample_documents, [])

    def test_no_event_drivers(self, sample_documents, unknown_document):
        config = PipelineConfig(
            distance_function={"name": "cosine"},
            analysis_method={"name": "nearest_neighbor"},
        )
        with pytest.raises(PipelineError, match="event driver"):
            Pipeline(config).execute(sample_documents, [unknown_document])

    def test_missing_distance_function(self, sample_documents, unknown_document):
        config = PipelineConfig(
            event_drivers=[{"name": "word_events"}],
            analysis_method={"name": "nearest_neighbor"},
        )
        with pytest.raises(PipelineError, match="distance function"):
            Pipeline(config).execute(sample_documents, [unknown_document])

    def test_progress_callback(self, sample_documents, unknown_document):
        progress_log = []

        def on_progress(fraction, message):
            progress_log.append((fraction, message))

        config = PipelineConfig(
            event_drivers=[{"name": "word_events"}],
            distance_function={"name": "cosine"},
            analysis_method={"name": "nearest_neighbor"},
        )
        Pipeline(config, progress_callback=on_progress).execute(
            sample_documents, [unknown_document]
        )
        assert len(progress_log) > 0
        # Should start near 0 and end near 1
        assert progress_log[0][0] < 0.5
        assert progress_log[-1][0] >= 0.9

    def test_multiple_unknown_documents(self, sample_documents):
        unknowns = [
            Document(text="The quick fox runs."),
            Document(text="The lazy dog rests."),
        ]
        config = PipelineConfig(
            event_drivers=[{"name": "character_ngram", "params": {"n": 3}}],
            distance_function={"name": "cosine"},
            analysis_method={"name": "nearest_neighbor"},
        )
        results = Pipeline(config).execute(sample_documents, unknowns)
        assert len(results) == 2
        assert results[0].unknown_document is unknowns[0]
        assert results[1].unknown_document is unknowns[1]

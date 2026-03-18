"""Tests for topic-controlled evaluation."""

import pytest

from mowen.evaluation import topic_controlled_evaluate
from mowen.exceptions import EvaluationError
from mowen.pipeline import PipelineConfig
from mowen.types import Document


def _config():
    return PipelineConfig(
        event_drivers=[{"name": "character_ngram", "params": {"n": 3}}],
        distance_function={"name": "cosine"},
        analysis_method={"name": "nearest_neighbor"},
    )


def _make_topic_docs():
    """Two topics, two authors, 2 docs each per topic."""
    return [
        Document(
            text="The government requires strong institutions.",
            author="Hamilton",
            title="h_pol",
            metadata={"topic": "politics"},
        ),
        Document(
            text="Federal power ensures defense.",
            author="Hamilton",
            title="h_pol2",
            metadata={"topic": "politics"},
        ),
        Document(
            text="Separation of powers prevents tyranny.",
            author="Madison",
            title="m_pol",
            metadata={"topic": "politics"},
        ),
        Document(
            text="A republic guards against faction.",
            author="Madison",
            title="m_pol2",
            metadata={"topic": "politics"},
        ),
        Document(
            text="Economics drives trade between nations.",
            author="Hamilton",
            title="h_econ",
            metadata={"topic": "economics"},
        ),
        Document(
            text="Banks and currency stabilize the economy.",
            author="Hamilton",
            title="h_econ2",
            metadata={"topic": "economics"},
        ),
        Document(
            text="Agriculture is the foundation of wealth.",
            author="Madison",
            title="m_econ",
            metadata={"topic": "economics"},
        ),
        Document(
            text="Land ownership drives economic independence.",
            author="Madison",
            title="m_econ2",
            metadata={"topic": "economics"},
        ),
    ]


class TestTopicControlledEvaluation:
    def test_basic_topic_controlled(self):
        docs = _make_topic_docs()
        result = topic_controlled_evaluate(docs, _config())
        assert result.overall is not None
        assert result.across_topic is not None
        assert len(result.within_topic) == 2
        assert "politics" in result.within_topic
        assert "economics" in result.within_topic

    def test_overall_matches_loo(self):
        """Overall result should be same as standard LOO."""
        from mowen.evaluation import leave_one_out

        docs = _make_topic_docs()
        tc = topic_controlled_evaluate(docs, _config())
        loo = leave_one_out(docs, _config())
        assert tc.overall.accuracy == pytest.approx(loo.accuracy)

    def test_missing_topic_raises(self):
        docs = [
            Document(text="text", author="A", title="d1"),
            Document(text="text", author="B", title="d2"),
        ]
        with pytest.raises(EvaluationError, match="missing metadata"):
            topic_controlled_evaluate(docs, _config())

    def test_accuracies_in_range(self):
        docs = _make_topic_docs()
        result = topic_controlled_evaluate(docs, _config())
        assert 0.0 <= result.overall.accuracy <= 1.0
        assert 0.0 <= result.across_topic.accuracy <= 1.0
        for r in result.within_topic.values():
            assert 0.0 <= r.accuracy <= 1.0

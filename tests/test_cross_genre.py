"""Tests for cross-genre evaluation."""

import pytest

from mowen.evaluation import cross_genre_evaluate
from mowen.exceptions import EvaluationError
from mowen.pipeline import PipelineConfig
from mowen.types import Document


def _config():
    return PipelineConfig(
        event_drivers=[{"name": "character_ngram", "params": {"n": 3}}],
        distance_function={"name": "cosine"},
        analysis_method={"name": "nearest_neighbor"},
    )


def _make_cross_genre_docs():
    """Two genres (formal/informal), two authors, multiple docs each."""
    return [
        Document(
            text="The government requires strong institutions.",
            author="Hamilton",
            title="h_formal1",
            metadata={"genre": "formal"},
        ),
        Document(
            text="Federal power ensures national defense.",
            author="Hamilton",
            title="h_formal2",
            metadata={"genre": "formal"},
        ),
        Document(
            text="Separation of powers prevents tyranny.",
            author="Madison",
            title="m_formal1",
            metadata={"genre": "formal"},
        ),
        Document(
            text="A republic guards against faction dangers.",
            author="Madison",
            title="m_formal2",
            metadata={"genre": "formal"},
        ),
        Document(
            text="gov needs to be strong, institutions matter!",
            author="Hamilton",
            title="h_informal1",
            metadata={"genre": "informal"},
        ),
        Document(
            text="we need federal power for defense!",
            author="Hamilton",
            title="h_informal2",
            metadata={"genre": "informal"},
        ),
        Document(
            text="separation of powers stops tyranny imo",
            author="Madison",
            title="m_informal1",
            metadata={"genre": "informal"},
        ),
        Document(
            text="republic keeps factions in check tbh",
            author="Madison",
            title="m_informal2",
            metadata={"genre": "informal"},
        ),
    ]


class TestCrossGenreEvaluation:
    def test_basic_cross_genre(self):
        docs = _make_cross_genre_docs()
        result = cross_genre_evaluate(
            docs,
            _config(),
            "formal",
            "informal",
        )
        assert result is not None
        assert 0.0 <= result.accuracy <= 1.0
        assert len(result.per_author) == 2

    def test_missing_genre_raises(self):
        docs = _make_cross_genre_docs()
        with pytest.raises(EvaluationError, match="No documents"):
            cross_genre_evaluate(
                docs,
                _config(),
                "formal",
                "nonexistent",
            )

    def test_no_shared_authors_raises(self):
        docs = [
            Document(
                text="text",
                author="OnlyFormal",
                title="f1",
                metadata={"genre": "formal"},
            ),
            Document(
                text="text",
                author="OnlyFormal",
                title="f2",
                metadata={"genre": "formal"},
            ),
            Document(
                text="text",
                author="OnlyInformal",
                title="i1",
                metadata={"genre": "informal"},
            ),
            Document(
                text="text",
                author="OnlyInformal",
                title="i2",
                metadata={"genre": "informal"},
            ),
        ]
        with pytest.raises(EvaluationError, match="shared authors"):
            cross_genre_evaluate(
                docs,
                _config(),
                "formal",
                "informal",
            )

    def test_all_authors_in_results(self):
        docs = _make_cross_genre_docs()
        result = cross_genre_evaluate(
            docs,
            _config(),
            "formal",
            "informal",
        )
        authors = {a.author for a in result.per_author}
        assert authors == {"Hamilton", "Madison"}

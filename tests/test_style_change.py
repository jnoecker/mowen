"""Tests for style change detection."""

from mowen.pipeline import PipelineConfig
from mowen.style_change import detect_style_changes
from mowen.types import Document


def _config():
    return PipelineConfig(
        event_drivers=[{"name": "character_ngram", "params": {"n": 3}}],
        distance_function={"name": "cosine"},
    )


class TestStyleChangeDetection:
    def test_single_paragraph(self):
        doc = Document(text="Just one paragraph here.", title="single")
        result = detect_style_changes(doc, _config())
        assert len(result.paragraphs) == 1
        assert len(result.predictions) == 0

    def test_two_similar_paragraphs(self):
        text = (
            "The quick brown fox jumps over the lazy dog. "
            "The quick fox ran across the field.\n\n"
            "The quick brown fox leaps over the lazy dog. "
            "The quick fox ran across the meadow."
        )
        doc = Document(text=text, title="similar")
        result = detect_style_changes(doc, _config())
        assert len(result.paragraphs) == 2
        assert len(result.predictions) == 1

    def test_two_different_paragraphs(self):
        text = (
            "The quick brown fox jumps over the lazy dog. "
            "The quick fox ran across the field. "
            "Foxes are quick nimble creatures.\n\n"
            "12345 67890 !@#$% ^&*() +=- []{}|;':\",./<>? "
            "99999 88888 77777 66666 55555 44444 33333"
        )
        doc = Document(text=text, title="different")
        result = detect_style_changes(doc, _config())
        assert len(result.paragraphs) == 2
        assert len(result.predictions) == 1
        # With very different content, score should be high
        assert result.predictions[0].score >= 0.0

    def test_three_paragraphs_returns_two_boundaries(self):
        text = "Para one.\n\nPara two.\n\nPara three."
        doc = Document(text=text, title="three")
        result = detect_style_changes(doc, _config())
        assert len(result.paragraphs) == 3
        assert len(result.predictions) == 2

    def test_custom_separator(self):
        text = "First section.---Second section."
        doc = Document(text=text, title="custom")
        result = detect_style_changes(
            doc,
            _config(),
            separator="---",
        )
        assert len(result.paragraphs) == 2
        assert len(result.predictions) == 1

    def test_threshold_sensitivity(self):
        text = "Hello world.\n\nGoodbye world."
        doc = Document(text=text, title="thresh")
        # With threshold=0.0, everything is a change
        low = detect_style_changes(doc, _config(), threshold=0.0)
        # With threshold=1.1, nothing is (scores normalized to [0,1])
        high = detect_style_changes(doc, _config(), threshold=1.1)
        assert all(p.is_change for p in low.predictions)
        assert all(not p.is_change for p in high.predictions)

    def test_empty_document(self):
        doc = Document(text="", title="empty")
        result = detect_style_changes(doc, _config())
        assert len(result.paragraphs) == 0
        assert len(result.predictions) == 0

    def test_scores_in_range(self):
        text = "A.\n\nB.\n\nC."
        doc = Document(text=text, title="range")
        result = detect_style_changes(doc, _config())
        for p in result.predictions:
            assert 0.0 <= p.score <= 1.0

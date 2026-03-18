"""Tests for the LLM zero-shot prompting analysis method."""

from unittest.mock import patch

from mowen.analysis_methods import analysis_method_registry
from mowen.types import Document, Event, Histogram


def _make_training_data():
    doc_a = Document(text="The fox is quick.", author="A", title="a1")
    hist_a = Histogram({Event("fox"): 3, Event("quick"): 2})
    doc_b = Document(text="The dog is slow.", author="B", title="b1")
    hist_b = Histogram({Event("dog"): 3, Event("slow"): 2})
    return [(doc_a, hist_a), (doc_b, hist_b)]


class TestLLMPrompting:
    def test_registered(self):
        assert "llm_prompting" in analysis_method_registry.names()

    def test_lower_is_better_false(self):
        method = analysis_method_registry.create("llm_prompting")
        assert method.lower_is_better is False

    def test_param_defs(self):
        method = analysis_method_registry.create("llm_prompting")
        param_names = {p.name for p in method.param_defs()}
        assert "provider" in param_names
        assert "model_name" in param_names
        assert "prompt_style" in param_names
        assert "max_known_chars" in param_names

    def test_all_prompt_styles(self):
        """Each prompt style should produce a valid prompt."""
        for style in ["no_guidance", "style", "grammar", "lip"]:
            method = analysis_method_registry.create(
                "llm_prompting", {"prompt_style": style}
            )
            method.train(_make_training_data())
            prompt = method._build_prompt("Some unknown text.")
            assert "A" in prompt
            assert "B" in prompt
            assert "unknown" in prompt.lower() or "Some" in prompt

    def test_parse_response_json(self):
        method = analysis_method_registry.create("llm_prompting")
        method.train(_make_training_data())

        response = '{"author": "A", "ranking": ["A", "B"]}'
        results = method._parse_response(response)
        assert results[0].author == "A"
        assert results[1].author == "B"
        assert results[0].score > results[1].score

    def test_parse_response_json_with_surrounding_text(self):
        """JSON embedded in explanatory text should still be extracted."""
        method = analysis_method_registry.create("llm_prompting")
        method.train(_make_training_data())

        response = (
            "Based on my analysis of the writing styles, "
            'here is my attribution: {"author": "B", "ranking": ["B", "A"]}. '
            "The key indicators were vocabulary choice."
        )
        results = method._parse_response(response)
        assert results[0].author == "B"

    def test_parse_response_json_validates_author_names(self):
        """JSON with unknown author names should be rejected."""
        method = analysis_method_registry.create("llm_prompting")
        method.train(_make_training_data())

        response = '{"author": "Unknown Person", "ranking": ["Unknown Person"]}'
        results = method._parse_response(response)
        # Should fall back, not return "Unknown Person"
        assert all(r.author in ("A", "B") for r in results)

    def test_parse_response_malformed_json(self):
        """Malformed JSON should fall back to text matching."""
        method = analysis_method_registry.create("llm_prompting")
        method.train(_make_training_data())

        response = '{"author": "A", ranking: [broken json}. I think A wrote it.'
        results = method._parse_response(response)
        assert len(results) == 2

    def test_parse_response_fallback_uses_last_mention(self):
        """Text fallback should prefer the last-mentioned author."""
        method = analysis_method_registry.create("llm_prompting")
        method.train(_make_training_data())

        response = (
            "A is a possible candidate based on vocabulary. "
            "However, B is unlikely due to sentence structure. "
            "After careful analysis, the author is most likely A."
        )
        results = method._parse_response(response)
        # A is mentioned last, should rank first
        assert results[0].author == "A"

    def test_parse_response_fallback_tail_single_author(self):
        """When only one author appears in the tail, pick them."""
        method = analysis_method_registry.create("llm_prompting")
        method.train(_make_training_data())

        response = (
            "Both A and B have similar styles. "
            "A uses more formal language. "
            "B prefers shorter sentences. " * 10 +
            "In conclusion, the unknown text was written by A."
        )
        results = method._parse_response(response)
        assert results[0].author == "A"

    def test_parse_response_no_author_found(self):
        """When no author is found, all should still be present."""
        method = analysis_method_registry.create("llm_prompting")
        method.train(_make_training_data())

        response = "I cannot determine the author of this text."
        results = method._parse_response(response)
        assert len(results) == 2
        authors = {r.author for r in results}
        assert authors == {"A", "B"}

    def test_all_authors_present_in_results(self):
        method = analysis_method_registry.create("llm_prompting")
        method.train(_make_training_data())

        response = '{"author": "A", "ranking": ["A"]}'
        results = method._parse_response(response)
        authors = {r.author for r in results}
        assert authors == {"A", "B"}

    @patch(
        "mowen.analysis_methods.llm_prompting.LLMPrompting._call_llm"
    )
    def test_analyze_with_mocked_api(self, mock_call):
        mock_call.return_value = (
            '{"author": "A", "ranking": ["A", "B"]}'
        )
        method = analysis_method_registry.create("llm_prompting")
        method.train(_make_training_data())

        unknown = Histogram({Event("fox"): 2, Event("quick"): 1})
        results = method.analyze(unknown)

        assert len(results) == 2
        assert results[0].author == "A"
        mock_call.assert_called_once()

"""Tests for the LLM zero-shot prompting analysis method."""

from unittest.mock import MagicMock, patch

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

    def test_parse_response_fallback(self):
        """When JSON fails, should find author names in text."""
        method = analysis_method_registry.create("llm_prompting")
        method.train(_make_training_data())

        response = "I believe author B wrote this text because..."
        results = method._parse_response(response)
        assert any(r.author == "B" for r in results)
        assert len(results) == 2  # all authors present

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

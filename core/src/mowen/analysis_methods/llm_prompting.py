"""LLM zero-shot prompting for authorship attribution.

Uses a large language model to attribute unknown documents to known
authors via carefully constructed prompts.  Supports multiple prompting
strategies with increasing linguistic specificity.

Reference: Huang, Chen & Shu (EMNLP 2024), "Can Large Language Models
Identify Authorship?"
"""

from __future__ import annotations

import json as json_mod
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from mowen.analysis_methods.base import AnalysisMethod, analysis_method_registry
from mowen.parameters import ParamDef
from mowen.types import Attribution, Document, Histogram

_PROMPT_TEMPLATES = {
    "no_guidance": (
        "Here are texts by known authors:\n\n{known_texts}\n\n"
        "Which author most likely wrote this unknown text?\n\n"
        "{unknown_text}\n\n"
        'Respond with JSON: {{"author": "<name>", '
        '"ranking": ["<most likely>", "<2nd>", ...]}}'
    ),
    "style": (
        "Here are texts by known authors:\n\n{known_texts}\n\n"
        "Analyze the writing styles of these authors, disregarding "
        "differences in topic and content. Which author most likely "
        "wrote this unknown text?\n\n{unknown_text}\n\n"
        'Respond with JSON: {{"author": "<name>", '
        '"ranking": ["<most likely>", "<2nd>", ...]}}'
    ),
    "grammar": (
        "Here are texts by known authors:\n\n{known_texts}\n\n"
        "Focus on grammatical styles indicative of authorship: "
        "sentence structure, clause patterns, verb tense usage, "
        "and syntactic preferences. Which author most likely "
        "wrote this unknown text?\n\n{unknown_text}\n\n"
        'Respond with JSON: {{"author": "<name>", '
        '"ranking": ["<most likely>", "<2nd>", ...]}}'
    ),
    "lip": (
        "Here are texts by known authors:\n\n{known_texts}\n\n"
        "Analyze the writing styles of these texts, disregarding "
        "differences in topic and content. Reason based on "
        "linguistic features such as phrasal verbs, modal verbs, "
        "punctuation, rare words, affixes, quantities, humor, "
        "sarcasm, typographical errors, and misspellings. "
        "Which author most likely wrote this unknown text?\n\n"
        "{unknown_text}\n\n"
        'Respond with JSON: {{"author": "<name>", '
        '"ranking": ["<most likely>", "<2nd>", ...]}}'
    ),
}


@analysis_method_registry.register("llm_prompting")
@dataclass
class LLMPrompting(AnalysisMethod):
    """Attribute authorship via LLM zero-shot prompting.

    Constructs a prompt with known-author text excerpts and the unknown
    text, sends it to an LLM API, and parses the response for author
    rankings.  Supports Anthropic (Claude) and OpenAI providers.

    Requires the ``anthropic`` or ``openai`` package.

    Score semantics: higher = more likely (rank-based, 1.0 for top).
    """

    lower_is_better: bool = False

    display_name: str = "LLM Zero-Shot Prompting"
    description: str = (
        "Authorship attribution via LLM prompting "
        "(requires anthropic or openai package)."
    )

    _author_excerpts: dict[str, str] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="provider",
                description="LLM API provider.",
                param_type=str,
                default="anthropic",
                choices=["anthropic", "openai"],
            ),
            ParamDef(
                name="model_name",
                description="Model name for the API.",
                param_type=str,
                default="claude-sonnet-4-20250514",
            ),
            ParamDef(
                name="prompt_style",
                description=(
                    "Prompting strategy: no_guidance, style, "
                    "grammar, or lip (Linguistically Informed)."
                ),
                param_type=str,
                default="style",
                choices=["no_guidance", "style", "grammar", "lip"],
            ),
            ParamDef(
                name="max_known_chars",
                description="Max characters per author excerpt.",
                param_type=int,
                default=2000,
                min_value=100,
                max_value=50000,
            ),
        ]

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Build author excerpts from known documents."""
        super().train(known_docs)

        max_chars: int = self.get_param("max_known_chars")

        author_texts: dict[str, list[str]] = defaultdict(list)
        for doc, _ in self._known_docs:
            author = doc.author or ""
            author_texts[author].append(doc.text)

        self._author_excerpts = {}
        for author, texts in author_texts.items():
            combined = "\n\n".join(texts)
            self._author_excerpts[author] = combined[:max_chars]

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Query LLM and return author rankings."""
        # Find the unknown document text from stored known docs
        # (the histogram alone doesn't carry the text, so we reconstruct)
        unknown_text = self._reconstruct_text(unknown_histogram)

        prompt = self._build_prompt(unknown_text)
        response = self._call_llm(prompt)
        return self._parse_response(response)

    def _reconstruct_text(self, histogram: Histogram) -> str:
        """Reconstruct text from histogram events."""
        tokens = []
        for event in histogram.unique_events():
            tokens.extend([event.data] * histogram.absolute_frequency(event))
        return " ".join(tokens)

    def _build_prompt(self, unknown_text: str) -> str:
        """Construct the attribution prompt."""
        style: str = self.get_param("prompt_style")
        template = _PROMPT_TEMPLATES[style]

        known_parts = []
        for author, excerpt in self._author_excerpts.items():
            known_parts.append(f"--- {author} ---\n{excerpt}")
        known_texts = "\n\n".join(known_parts)

        return template.format(
            known_texts=known_texts,
            unknown_text=unknown_text,
        )

    def _call_llm(self, prompt: str) -> str:
        """Call the LLM API and return the response text."""
        provider: str = self.get_param("provider")
        model: str = self.get_param("model_name")

        if provider == "anthropic":
            return self._call_anthropic(prompt, model)
        else:
            return self._call_openai(prompt, model)

    def _call_anthropic(self, prompt: str, model: str) -> str:
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "LLM prompting with Anthropic requires the "
                "anthropic package. Install with: "
                "pip install anthropic"
            ) from exc

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def _call_openai(self, prompt: str, model: str) -> str:
        try:
            import openai
        except ImportError as exc:
            raise ImportError(
                "LLM prompting with OpenAI requires the openai "
                "package. Install with: pip install openai"
            ) from exc

        api_key = os.environ.get("OPENAI_API_KEY", "")
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""

    def _parse_response(self, response: str) -> list[Attribution]:
        """Parse LLM response into Attribution list."""
        authors = list(self._author_excerpts.keys())

        # Try to extract JSON from response
        ranking: list[str] = []
        try:
            # Find JSON in the response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json_mod.loads(response[start:end])
                if "ranking" in data:
                    ranking = data["ranking"]
                elif "author" in data:
                    ranking = [data["author"]]
        except (json_mod.JSONDecodeError, KeyError, TypeError):
            pass

        # Fallback: look for author names in response text
        if not ranking:
            for author in authors:
                if author in response:
                    ranking.append(author)

        # Ensure all authors appear in ranking
        seen = set(ranking)
        for author in authors:
            if author not in seen:
                ranking.append(author)

        # Assign decreasing scores by rank position
        n = len(ranking)
        return [
            Attribution(
                author=author,
                score=(n - i) / n if n > 0 else 0.0,
            )
            for i, author in enumerate(ranking)
            if author in self._author_excerpts
        ]

"""Tests for multi-language function word lists."""

from __future__ import annotations

import pytest

from mowen.data import available_languages, load_function_words
from mowen.event_drivers import event_driver_registry

EXPECTED_LANGUAGES = [
    "arabic",
    "chinese",
    "english",
    "french",
    "german",
    "italian",
    "japanese",
    "portuguese",
    "russian",
    "spanish",
]


class TestLoadFunctionWords:
    @pytest.mark.parametrize("language", EXPECTED_LANGUAGES)
    def test_language_loads(self, language):
        words = load_function_words(language)
        assert isinstance(words, frozenset)
        assert len(words) > 10, f"{language} has too few function words: {len(words)}"

    def test_english_contains_expected(self):
        words = load_function_words("english")
        assert "the" in words
        assert "and" in words
        assert "is" in words

    def test_chinese_contains_expected(self):
        words = load_function_words("chinese")
        assert "的" in words
        assert "是" in words
        assert "在" in words

    def test_spanish_contains_expected(self):
        words = load_function_words("spanish")
        assert "el" in words
        assert "de" in words
        assert "y" in words

    def test_case_insensitive(self):
        words = load_function_words("English")
        assert "the" in words

    def test_unknown_language_raises(self):
        with pytest.raises(FileNotFoundError, match="No function word list"):
            load_function_words("klingon")

    def test_no_duplicates(self):
        """The frozenset handles dedup, but verify file has no blank lines turned into entries."""
        words = load_function_words("english")
        assert "" not in words


class TestAvailableLanguages:
    def test_lists_all_languages(self):
        langs = available_languages()
        for expected in EXPECTED_LANGUAGES:
            assert expected in langs, f"Missing language: {expected}"


class TestFunctionWordsDriver:
    def test_english_default(self):
        d = event_driver_registry.create("function_words")
        es = d.create_event_set("the cat sat on the mat")
        words = [e.data for e in es]
        assert "the" in words
        assert "on" in words
        assert "cat" not in words

    def test_spanish(self):
        d = event_driver_registry.create("function_words", {"language": "spanish"})
        es = d.create_event_set("el gato se sentó en la alfombra")
        words = [e.data for e in es]
        assert "el" in words
        assert "en" in words
        assert "la" in words

    def test_unknown_language_raises(self):
        d = event_driver_registry.create("function_words", {"language": "klingon"})
        with pytest.raises(FileNotFoundError):
            d.create_event_set("some text")

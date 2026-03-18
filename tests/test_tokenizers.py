"""Tests for the tokenizer module."""

from __future__ import annotations

import pytest

from mowen.tokenizers import tokenizer_registry, tokenize_text


class TestWhitespaceTokenizer:
    def test_basic(self):
        tok = tokenizer_registry.create("whitespace")
        assert tok.tokenize("hello world") == ["hello", "world"]

    def test_multiple_spaces(self):
        tok = tokenizer_registry.create("whitespace")
        assert tok.tokenize("hello   world") == ["hello", "world"]

    def test_empty(self):
        tok = tokenizer_registry.create("whitespace")
        assert tok.tokenize("") == []

    def test_tabs_and_newlines(self):
        tok = tokenizer_registry.create("whitespace")
        assert tok.tokenize("a\tb\nc") == ["a", "b", "c"]


class TestTokenizeText:
    def test_default_whitespace(self):
        assert tokenize_text("hello world") == ["hello", "world"]

    def test_explicit_whitespace(self):
        assert tokenize_text("hello world", "whitespace") == ["hello", "world"]


class TestJiebaTokenizer:
    def test_jieba_registered(self):
        """Jieba tokenizer should be registered even if jieba isn't installed."""
        assert "jieba" in tokenizer_registry.names()

    def test_jieba_import_error(self):
        """If jieba is not installed, tokenize should raise ImportError."""
        try:
            import jieba  # noqa: F401

            pytest.skip("jieba is installed; cannot test import error")
        except ImportError:
            tok = tokenizer_registry.create("jieba")
            with pytest.raises(ImportError, match="jieba"):
                tok.tokenize("你好世界")


class TestTokenizerRegistry:
    def test_whitespace_registered(self):
        assert "whitespace" in tokenizer_registry.names()

    def test_list_all(self):
        all_tokenizers = tokenizer_registry.list_all()
        assert len(all_tokenizers) >= 2  # whitespace + jieba


class TestDriverTokenizerParam:
    """Verify that word-based drivers accept the tokenizer parameter."""

    WORD_DRIVERS = [
        "word_events",
        "word_ngram",
        "word_length",
        "rare_words",
        "vowel_initial_words",
        "function_words",
        "mw_function_words",
        "mn_letter_words",
        "sentence_length",
        "first_word_in_sentence",
        "porter_stemmer",
        "k_skip_word_ngram",
        "sorted_word_ngram",
    ]

    @pytest.mark.parametrize("driver_name", WORD_DRIVERS)
    def test_has_tokenizer_param(self, driver_name):
        from mowen.event_drivers import event_driver_registry

        cls = event_driver_registry.get(driver_name)
        param_names = [p.name for p in cls.param_defs()]
        assert "tokenizer" in param_names, f"{driver_name} missing tokenizer param"

    @pytest.mark.parametrize("driver_name", WORD_DRIVERS)
    def test_default_tokenizer_works(self, driver_name):
        """Drivers should produce events with default tokenizer (whitespace)."""
        from mowen.event_drivers import event_driver_registry

        driver = event_driver_registry.create(driver_name)
        es = driver.create_event_set("The quick brown fox jumps over the lazy dog.")
        # Should produce at least some events (may vary by driver)
        # Just verify no crash
        assert isinstance(es, list)

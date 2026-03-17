"""Tests for NER and definition event drivers."""

from __future__ import annotations

import pytest

from mowen.event_drivers import event_driver_registry
from mowen.types import Event


class TestNamedEntities:
    def test_registered(self):
        assert "named_entities" in event_driver_registry.names()

    def test_import_error_without_spacy(self):
        try:
            import spacy  # noqa: F401
            pytest.skip("spaCy is installed and functional")
        except (ImportError, Exception):
            # spaCy not installed or broken (e.g. pydantic v1 on Python 3.14)
            d = event_driver_registry.create("named_entities")
            with pytest.raises((ImportError, Exception)):
                d.create_event_set("John went to New York")


class TestEntityText:
    def test_registered(self):
        assert "entity_text" in event_driver_registry.names()


class TestEntityContext:
    def test_registered(self):
        assert "entity_context" in event_driver_registry.names()


class TestDefinitionEvents:
    def test_registered(self):
        assert "definitions" in event_driver_registry.names()

    def test_import_error_without_nltk(self):
        try:
            from nltk.corpus import wordnet  # noqa: F401
            # Also check that wordnet data is actually available
            wordnet.synsets("test")
            pytest.skip("NLTK with WordNet is installed")
        except (ImportError, LookupError):
            d = event_driver_registry.create("definitions")
            with pytest.raises((ImportError, LookupError)):
                d.create_event_set("the cat sat on the mat")

    def test_with_wordnet(self):
        """If NLTK+WordNet are available, verify basic functionality."""
        try:
            from nltk.corpus import wordnet  # noqa: F401
            wordnet.synsets("test")
        except (ImportError, LookupError):
            pytest.skip("NLTK with WordNet not available")

        d = event_driver_registry.create("definitions")
        es = d.create_event_set("cat dog")
        # Should produce some definition words
        assert len(es) > 0
        # All events should be lowercase non-stop words
        for e in es:
            assert e.data == e.data.lower()
            assert len(e.data) > 1

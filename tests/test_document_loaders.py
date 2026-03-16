"""Tests for document loaders."""

import tempfile
from pathlib import Path

import pytest

from mowen.document_loaders import PlainTextLoader, load_document
from mowen.exceptions import DocumentLoadError


class TestPlainTextLoader:
    def test_load_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello, world!", encoding="utf-8")
        loader = PlainTextLoader()
        doc = loader.load(f, author="Test Author")
        assert doc.text == "Hello, world!"
        assert doc.author == "Test Author"
        assert doc.title == "test"

    def test_custom_title(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("content", encoding="utf-8")
        doc = PlainTextLoader().load(f, title="Custom")
        assert doc.title == "Custom"

    def test_file_not_found(self):
        with pytest.raises(DocumentLoadError, match="not found"):
            PlainTextLoader().load(Path("/nonexistent/file.txt"))


class TestLoadDocument:
    def test_auto_detect_txt(self, tmp_path):
        f = tmp_path / "doc.txt"
        f.write_text("Some text", encoding="utf-8")
        doc = load_document(str(f), author="Author")
        assert doc.text == "Some text"
        assert doc.author == "Author"

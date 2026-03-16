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


class TestPlainTextLoaderEdgeCases:
    def test_latin1_fallback(self, tmp_path):
        """Latin-1 encoded files should be loadable with a fallback."""
        f = tmp_path / "latin1.txt"
        f.write_bytes("caf\xe9".encode("latin-1"))
        doc = PlainTextLoader().load(f)
        assert doc.text == "caf\xe9"

    def test_utf8_with_bom(self, tmp_path):
        """UTF-8 files with BOM should load correctly."""
        f = tmp_path / "bom.txt"
        f.write_bytes(b"\xef\xbb\xbfHello BOM")
        doc = PlainTextLoader().load(f)
        assert "Hello BOM" in doc.text

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        doc = PlainTextLoader().load(f)
        assert doc.text == ""

    def test_unicode_content(self, tmp_path):
        """Unicode characters beyond ASCII should be preserved."""
        f = tmp_path / "unicode.txt"
        f.write_text("Hello \u4e16\u754c \u00e9\u00e0\u00fc", encoding="utf-8")
        doc = PlainTextLoader().load(f)
        assert "\u4e16\u754c" in doc.text
        assert "\u00e9" in doc.text

    def test_default_title_is_stem(self, tmp_path):
        f = tmp_path / "my_document.txt"
        f.write_text("content", encoding="utf-8")
        doc = PlainTextLoader().load(f)
        assert doc.title == "my_document"


class TestLoadDocument:
    def test_auto_detect_txt(self, tmp_path):
        f = tmp_path / "doc.txt"
        f.write_text("Some text", encoding="utf-8")
        doc = load_document(str(f), author="Author")
        assert doc.text == "Some text"
        assert doc.author == "Author"

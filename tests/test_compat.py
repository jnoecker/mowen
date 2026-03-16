"""Tests for compatibility utilities."""

from __future__ import annotations

from mowen.compat.jgaap_csv import load_jgaap_csv


class TestJgaapCsv:
    def test_load_basic(self, tmp_path):
        (tmp_path / "a.txt").write_text("text a", encoding="utf-8")
        (tmp_path / "b.txt").write_text("text b", encoding="utf-8")
        (tmp_path / "u.txt").write_text("text u", encoding="utf-8")
        csv = tmp_path / "exp.csv"
        csv.write_text("a.txt,AuthorA\nb.txt,AuthorB\nu.txt,\n", encoding="utf-8")

        known, unknown = load_jgaap_csv(csv)
        assert len(known) == 2
        assert len(unknown) == 1
        assert known[0].author == "AuthorA"
        assert known[1].author == "AuthorB"
        assert unknown[0].author is None

    def test_load_with_base_dir(self, tmp_path):
        subdir = tmp_path / "docs"
        subdir.mkdir()
        (subdir / "a.txt").write_text("text a", encoding="utf-8")
        csv = tmp_path / "exp.csv"
        csv.write_text("a.txt,AuthorA\n", encoding="utf-8")

        known, _ = load_jgaap_csv(csv, base_dir=subdir)
        assert len(known) == 1
        assert known[0].text == "text a"

    def test_skips_blank_lines(self, tmp_path):
        (tmp_path / "a.txt").write_text("text", encoding="utf-8")
        csv = tmp_path / "exp.csv"
        csv.write_text("\na.txt,AuthorA\n\n", encoding="utf-8")

        known, unknown = load_jgaap_csv(csv)
        assert len(known) == 1
        assert len(unknown) == 0

    def test_empty_csv(self, tmp_path):
        csv = tmp_path / "empty.csv"
        csv.write_text("", encoding="utf-8")
        known, unknown = load_jgaap_csv(csv)
        assert known == []
        assert unknown == []

"""Tests for the mowen CLI."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from mowen_cli.main import app

runner = CliRunner()


class TestHelp:
    def test_main_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "attribution" in result.output.lower()

    def test_run_help(self):
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--documents" in result.output

    def test_list_components_help(self):
        result = runner.invoke(app, ["list-components", "--help"])
        assert result.exit_code == 0

    def test_convert_jgaap_help(self):
        result = runner.invoke(app, ["convert-jgaap", "--help"])
        assert result.exit_code == 0


class TestListComponents:
    def test_list_all(self):
        result = runner.invoke(app, ["list-components"])
        assert result.exit_code == 0
        assert "canonicizers" in result.output
        assert "event-drivers" in result.output
        assert "distance-functions" in result.output
        assert "analysis-methods" in result.output

    def test_list_single_category(self):
        result = runner.invoke(app, ["list-components", "canonicizers"])
        assert result.exit_code == 0
        assert "unify_case" in result.output
        assert "distance-functions" not in result.output

    def test_list_unknown_category(self):
        result = runner.invoke(app, ["list-components", "bogus"])
        assert result.exit_code == 1

    def test_list_json(self):
        result = runner.invoke(app, ["list-components", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "canonicizers" in data
        assert "event-drivers" in data
        assert len(data["canonicizers"]) > 0
        first = data["canonicizers"][0]
        assert "name" in first
        assert "display_name" in first

    def test_list_single_category_json(self):
        result = runner.invoke(app, ["list-components", "analysis-methods", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "analysis-methods" in data
        names = {c["name"] for c in data["analysis-methods"]}
        assert "knn" in names
        assert "nearest_neighbor" in names

    def test_params_shown(self):
        result = runner.invoke(app, ["list-components", "event-drivers"])
        assert result.exit_code == 0
        assert "--n" in result.output  # character_ngram has param 'n'


class TestRun:
    def test_run_text_output(self, tmp_path):
        _write_corpus(tmp_path)
        result = runner.invoke(app, [
            "run", "-d", str(tmp_path / "manifest.csv"),
            "-e", "character_ngram:n=3",
            "--distance", "cosine",
            "-a", "nearest_neighbor",
        ])
        assert result.exit_code == 0, result.output
        assert "Author A" in result.output or "Author B" in result.output

    def test_run_json_output(self, tmp_path):
        _write_corpus(tmp_path)
        result = runner.invoke(app, [
            "run", "-d", str(tmp_path / "manifest.csv"),
            "-e", "word_events",
            "--distance", "manhattan",
            "-a", "knn:k=2",
            "--json",
        ])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert len(data) == 1
        assert "rankings" in data[0]
        assert len(data[0]["rankings"]) == 2

    def test_run_with_canonicizer_and_culler(self, tmp_path):
        _write_corpus(tmp_path)
        result = runner.invoke(app, [
            "run", "-d", str(tmp_path / "manifest.csv"),
            "-e", "character_ngram:n=2",
            "-c", "unify_case",
            "-c", "normalize_whitespace",
            "--culler", "most_common:n=20",
            "--distance", "cosine",
            "-a", "nearest_neighbor",
        ])
        assert result.exit_code == 0, result.output

    def test_run_multiple_event_drivers(self, tmp_path):
        _write_corpus(tmp_path)
        result = runner.invoke(app, [
            "run", "-d", str(tmp_path / "manifest.csv"),
            "-e", "character_ngram:n=3",
            "-e", "word_events",
            "--distance", "cosine",
            "-a", "nearest_neighbor",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1

    def test_run_missing_csv(self):
        result = runner.invoke(app, [
            "run", "-d", "/nonexistent.csv",
            "-e", "word_events",
        ])
        assert result.exit_code == 1

    def test_run_no_unknowns(self, tmp_path):
        # CSV with only known docs (all have authors)
        (tmp_path / "a.txt").write_text("some text", encoding="utf-8")
        (tmp_path / "manifest.csv").write_text("a.txt,AuthorA\n", encoding="utf-8")
        result = runner.invoke(app, [
            "run", "-d", str(tmp_path / "manifest.csv"),
            "-e", "word_events",
        ])
        assert result.exit_code == 1
        assert "unknown" in result.output.lower()


class TestConvertJgaap:
    def test_convert(self, tmp_path):
        _write_corpus(tmp_path)
        result = runner.invoke(app, ["convert-jgaap", str(tmp_path / "manifest.csv")])
        assert result.exit_code == 0
        assert "2 known" in result.output
        assert "1 unknown" in result.output
        assert "Author A" in result.output
        assert "Author B" in result.output

    def test_convert_missing_file(self):
        result = runner.invoke(app, ["convert-jgaap", "/nonexistent.csv"])
        assert result.exit_code == 1


def _write_corpus(tmp_path):
    """Write a minimal test corpus to tmp_path."""
    (tmp_path / "a1.txt").write_text(
        "The quick brown fox jumps over the lazy dog.", encoding="utf-8"
    )
    (tmp_path / "b1.txt").write_text(
        "A slow cat sleeps on the warm windowsill all day.", encoding="utf-8"
    )
    (tmp_path / "unknown.txt").write_text(
        "The fast fox leaps across the green meadow.", encoding="utf-8"
    )
    (tmp_path / "manifest.csv").write_text(
        "a1.txt,Author A\nb1.txt,Author B\nunknown.txt,\n", encoding="utf-8"
    )

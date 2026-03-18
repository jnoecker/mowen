"""Tests for the mowen CLI."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from mowen_cli.main import app

import re

runner = CliRunner()


def _strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


class TestHelp:
    def test_main_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "attribution" in _strip_ansi(result.output).lower()

    def test_run_help(self):
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--documents" in _strip_ansi(result.output)

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
        assert "canonicizers" in _strip_ansi(result.output)
        assert "event-drivers" in _strip_ansi(result.output)
        assert "distance-functions" in _strip_ansi(result.output)
        assert "analysis-methods" in _strip_ansi(result.output)

    def test_list_single_category(self):
        result = runner.invoke(app, ["list-components", "canonicizers"])
        assert result.exit_code == 0
        assert "unify_case" in _strip_ansi(result.output)
        assert "distance-functions" not in _strip_ansi(result.output)

    def test_list_unknown_category(self):
        result = runner.invoke(app, ["list-components", "bogus"])
        assert result.exit_code == 1

    def test_list_json(self):
        result = runner.invoke(app, ["list-components", "--json"])
        assert result.exit_code == 0
        data = json.loads(_strip_ansi(result.output))
        assert "canonicizers" in data
        assert "event-drivers" in data
        assert len(data["canonicizers"]) > 0
        first = data["canonicizers"][0]
        assert "name" in first
        assert "display_name" in first

    def test_list_single_category_json(self):
        result = runner.invoke(app, ["list-components", "analysis-methods", "--json"])
        assert result.exit_code == 0
        data = json.loads(_strip_ansi(result.output))
        assert "analysis-methods" in data
        names = {c["name"] for c in data["analysis-methods"]}
        assert "knn" in names
        assert "nearest_neighbor" in names

    def test_params_shown(self):
        result = runner.invoke(app, ["list-components", "event-drivers"])
        assert result.exit_code == 0
        assert "--n" in _strip_ansi(result.output)  # character_ngram has param 'n'


class TestRun:
    def test_run_text_output(self, tmp_path):
        _write_corpus(tmp_path)
        result = runner.invoke(
            app,
            [
                "run",
                "-d",
                str(tmp_path / "manifest.csv"),
                "-e",
                "character_ngram:n=3",
                "--distance",
                "cosine",
                "-a",
                "nearest_neighbor",
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)
        assert "Author A" in _strip_ansi(result.output) or "Author B" in _strip_ansi(
            result.output
        )

    def test_run_json_output(self, tmp_path):
        _write_corpus(tmp_path)
        result = runner.invoke(
            app,
            [
                "run",
                "-d",
                str(tmp_path / "manifest.csv"),
                "-e",
                "word_events",
                "--distance",
                "manhattan",
                "-a",
                "knn:k=2",
                "--json",
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)
        data = json.loads(_strip_ansi(result.output))
        assert len(data) == 1
        assert "rankings" in data[0]
        assert len(data[0]["rankings"]) == 2

    def test_run_with_canonicizer_and_culler(self, tmp_path):
        _write_corpus(tmp_path)
        result = runner.invoke(
            app,
            [
                "run",
                "-d",
                str(tmp_path / "manifest.csv"),
                "-e",
                "character_ngram:n=2",
                "-c",
                "unify_case",
                "-c",
                "normalize_whitespace",
                "--culler",
                "most_common:n=20",
                "--distance",
                "cosine",
                "-a",
                "nearest_neighbor",
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)

    def test_run_multiple_event_drivers(self, tmp_path):
        _write_corpus(tmp_path)
        result = runner.invoke(
            app,
            [
                "run",
                "-d",
                str(tmp_path / "manifest.csv"),
                "-e",
                "character_ngram:n=3",
                "-e",
                "word_events",
                "--distance",
                "cosine",
                "-a",
                "nearest_neighbor",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(_strip_ansi(result.output))
        assert len(data) == 1

    def test_run_missing_csv(self):
        result = runner.invoke(
            app,
            [
                "run",
                "-d",
                "/nonexistent.csv",
                "-e",
                "word_events",
            ],
        )
        assert result.exit_code == 1

    def test_run_verification_badges(self, tmp_path):
        """Verification methods should show VERIFIED/REJECTED badges."""
        _write_corpus(tmp_path)
        result = runner.invoke(
            app,
            [
                "run",
                "-d",
                str(tmp_path / "manifest.csv"),
                "-e",
                "character_ngram:n=3",
                "--distance",
                "cosine",
                "-a",
                "imposters:n_iterations=10,random_seed=42",
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)
        output = _strip_ansi(result.output)
        assert "VERIFIED" in output or "REJECTED" in output

    def test_run_verification_json(self, tmp_path):
        """JSON output should include verification_threshold and verified flag."""
        _write_corpus(tmp_path)
        result = runner.invoke(
            app,
            [
                "run",
                "-d",
                str(tmp_path / "manifest.csv"),
                "-e",
                "character_ngram:n=3",
                "--distance",
                "cosine",
                "-a",
                "imposters:n_iterations=10,random_seed=42",
                "--json",
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)
        data = json.loads(_strip_ansi(result.output))
        assert "verification_threshold" in data[0]
        assert "verdict" in data[0]
        assert data[0]["verdict"] in ("VERIFIED", "REJECTED", "INCONCLUSIVE")
        assert data[0]["verification_threshold"] == 0.5

    def test_run_no_unknowns(self, tmp_path):
        # CSV with only known docs (all have authors)
        (tmp_path / "a.txt").write_text("some text", encoding="utf-8")
        (tmp_path / "manifest.csv").write_text("a.txt,AuthorA\n", encoding="utf-8")
        result = runner.invoke(
            app,
            [
                "run",
                "-d",
                str(tmp_path / "manifest.csv"),
                "-e",
                "word_events",
            ],
        )
        assert result.exit_code == 1
        assert "unknown" in _strip_ansi(result.output).lower()


class TestConvertJgaap:
    def test_convert(self, tmp_path):
        _write_corpus(tmp_path)
        result = runner.invoke(app, ["convert-jgaap", str(tmp_path / "manifest.csv")])
        assert result.exit_code == 0
        assert "2 known" in _strip_ansi(result.output)
        assert "1 unknown" in _strip_ansi(result.output)
        assert "Author A" in _strip_ansi(result.output)
        assert "Author B" in _strip_ansi(result.output)

    def test_convert_missing_file(self):
        result = runner.invoke(app, ["convert-jgaap", "/nonexistent.csv"])
        assert result.exit_code == 1


class TestDetectChanges:
    def test_detect_changes_text_output(self, tmp_path):
        doc_path = _write_style_change_doc(tmp_path)
        result = runner.invoke(
            app,
            [
                "detect-changes",
                str(doc_path),
                "-e",
                "character_ngram:n=3",
                "--distance",
                "cosine",
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)
        output = _strip_ansi(result.output).lower()
        assert "change" in output or "same" in output

    def test_detect_changes_json_output(self, tmp_path):
        doc_path = _write_style_change_doc(tmp_path)
        result = runner.invoke(
            app,
            [
                "detect-changes",
                str(doc_path),
                "-e",
                "character_ngram:n=3",
                "--distance",
                "cosine",
                "--json",
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)
        data = json.loads(_strip_ansi(result.output))
        assert "boundaries" in data
        assert "paragraphs" in data

    def test_detect_changes_threshold(self, tmp_path):
        doc_path = _write_style_change_doc(tmp_path)
        # threshold=0.0 means everything is a change
        result = runner.invoke(
            app,
            [
                "detect-changes",
                str(doc_path),
                "-e",
                "character_ngram:n=3",
                "--distance",
                "cosine",
                "-t",
                "0.0",
                "--json",
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)
        data = json.loads(_strip_ansi(result.output))
        assert len(data["boundaries"]) > 0
        assert all(b["is_change"] for b in data["boundaries"])

    def test_detect_changes_custom_separator(self, tmp_path):
        text = (
            "The government must be strong and protect liberty. "
            "Federal power requires the authority of taxation."
            "---"
            "12345 67890 !@#$% ^&*() +=- []{}|;':,./<>? "
            "99999 88888 77777 66666 55555 44444 33333"
        )
        doc_path = tmp_path / "custom_sep.txt"
        doc_path.write_text(text, encoding="utf-8")
        result = runner.invoke(
            app,
            [
                "detect-changes",
                str(doc_path),
                "-e",
                "character_ngram:n=3",
                "--distance",
                "cosine",
                "--separator",
                "---",
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)
        output = _strip_ansi(result.output)
        assert "2 paragraphs" in output

    def test_detect_changes_single_paragraph(self, tmp_path):
        doc_path = tmp_path / "single.txt"
        doc_path.write_text(
            "This is a single paragraph with no breaks at all.",
            encoding="utf-8",
        )
        result = runner.invoke(
            app,
            [
                "detect-changes",
                str(doc_path),
                "-e",
                "character_ngram:n=3",
                "--distance",
                "cosine",
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)
        output = _strip_ansi(result.output)
        assert "0 change" in output

    def test_detect_changes_missing_file(self):
        result = runner.invoke(
            app,
            [
                "detect-changes",
                "/nonexistent_file.txt",
                "-e",
                "character_ngram:n=3",
            ],
        )
        assert result.exit_code == 1


class TestEvaluate:
    def test_evaluate_help(self):
        result = runner.invoke(app, ["evaluate", "--help"])
        assert result.exit_code == 0
        assert "--mode" in _strip_ansi(result.output)
        assert "--folds" in _strip_ansi(result.output)

    def test_evaluate_loo_text(self, tmp_path):
        _write_eval_corpus(tmp_path)
        result = runner.invoke(
            app,
            [
                "evaluate",
                "-d",
                str(tmp_path / "manifest.csv"),
                "-e",
                "character_ngram:n=3",
                "--distance",
                "cosine",
                "-a",
                "nearest_neighbor",
                "--mode",
                "loo",
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)
        assert "Accuracy" in _strip_ansi(result.output)
        assert "Confusion matrix" in _strip_ansi(result.output)

    def test_evaluate_kfold_json(self, tmp_path):
        _write_eval_corpus(tmp_path)
        result = runner.invoke(
            app,
            [
                "evaluate",
                "-d",
                str(tmp_path / "manifest.csv"),
                "-e",
                "word_events",
                "--distance",
                "manhattan",
                "-a",
                "nearest_neighbor",
                "--mode",
                "kfold",
                "-k",
                "2",
                "--seed",
                "42",
                "--json",
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)
        data = json.loads(_strip_ansi(result.output))
        assert "accuracy" in data
        assert "confusion_matrix" in data
        assert "per_author" in data

    def test_evaluate_csv_export(self, tmp_path):
        _write_eval_corpus(tmp_path)
        csv_path = tmp_path / "results.csv"
        result = runner.invoke(
            app,
            [
                "evaluate",
                "-d",
                str(tmp_path / "manifest.csv"),
                "-e",
                "character_ngram:n=3",
                "--distance",
                "cosine",
                "-a",
                "nearest_neighbor",
                "--mode",
                "loo",
                "-o",
                str(csv_path),
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)
        assert csv_path.exists()
        content = csv_path.read_text()
        assert "accuracy" in content

    def test_evaluate_json_has_verification_metrics(self, tmp_path):
        """JSON output should include eer and c_at_1 metrics."""
        _write_eval_corpus(tmp_path)
        result = runner.invoke(
            app,
            [
                "evaluate",
                "-d",
                str(tmp_path / "manifest.csv"),
                "-e",
                "character_ngram:n=3",
                "--distance",
                "cosine",
                "-a",
                "nearest_neighbor",
                "--mode",
                "loo",
                "--json",
            ],
        )
        assert result.exit_code == 0, _strip_ansi(result.output)
        data = json.loads(_strip_ansi(result.output))
        assert "eer" in data
        assert "c_at_1" in data

    def test_evaluate_single_author_error(self, tmp_path):
        (tmp_path / "a1.txt").write_text("hello world", encoding="utf-8")
        (tmp_path / "a2.txt").write_text("hello again", encoding="utf-8")
        (tmp_path / "manifest.csv").write_text(
            "a1.txt,SameAuthor\na2.txt,SameAuthor\n", encoding="utf-8"
        )
        result = runner.invoke(
            app,
            [
                "evaluate",
                "-d",
                str(tmp_path / "manifest.csv"),
                "-e",
                "word_events",
                "--mode",
                "loo",
            ],
        )
        assert result.exit_code == 1
        assert "author" in _strip_ansi(result.output).lower()


def _write_eval_corpus(tmp_path):
    """Write a corpus where all documents have authors (for evaluation)."""
    texts = {
        "ham1.txt": ("The government must be strong and protect liberty.", "Hamilton"),
        "ham2.txt": ("Federal power requires the authority of taxation.", "Hamilton"),
        "ham3.txt": ("A strong union ensures national defense and order.", "Hamilton"),
        "mad1.txt": ("Separation of powers prevents tyranny in republics.", "Madison"),
        "mad2.txt": (
            "Factions are controlled by the diversity of interests.",
            "Madison",
        ),
        "mad3.txt": (
            "A large republic guards against the danger of faction.",
            "Madison",
        ),
    }
    lines = []
    for fname, (text, author) in texts.items():
        (tmp_path / fname).write_text(text, encoding="utf-8")
        lines.append(f"{fname},{author}")
    (tmp_path / "manifest.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


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


def _write_style_change_doc(tmp_path):
    """Write a multi-paragraph document for style change detection."""
    text = (
        "The government must be strong and protect liberty. "
        "Federal power requires the authority of taxation.\n\n"
        "12345 67890 !@#$% ^&*() +=- []{}|;':,./<>? "
        "99999 88888 77777 66666 55555 44444 33333"
    )
    doc_path = tmp_path / "multi_author.txt"
    doc_path.write_text(text, encoding="utf-8")
    return doc_path

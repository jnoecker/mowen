"""Data files and loaders for mowen (function word lists, sample corpora, etc.)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=32)
def load_function_words(language: str) -> frozenset[str]:
    """Load the function word list for a language.

    Parameters
    ----------
    language:
        Language name (e.g. ``"english"``, ``"chinese"``).
        Case-insensitive.

    Returns
    -------
    frozenset[str]
        The set of function words, one per line in the source file,
        stripped and lowercased.

    Raises
    ------
    FileNotFoundError
        If no word list exists for the given language.
    """
    lang = language.lower()
    data_dir = Path(__file__).parent / "function_words"
    word_file = data_dir / f"{lang}.txt"
    if not word_file.exists():
        available = sorted(p.stem for p in data_dir.glob("*.txt"))
        raise FileNotFoundError(
            f"No function word list for language {language!r}. "
            f"Available: {', '.join(available)}"
        )
    text = word_file.read_text(encoding="utf-8")
    words = set()
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            words.add(line.lower())
    return frozenset(words)


def available_languages() -> list[str]:
    """Return the list of languages with function word lists."""
    data_dir = Path(__file__).parent / "function_words"
    return sorted(p.stem for p in data_dir.glob("*.txt"))


# ---------------------------------------------------------------------------
# Sample corpora (AAAC problem sets)
# ---------------------------------------------------------------------------

_SAMPLE_CORPORA_DIR = Path(__file__).parent / "sample_corpora"


@lru_cache(maxsize=1)
def _load_manifest() -> list[dict[str, Any]]:
    """Load and cache the sample corpora manifest."""
    manifest_path = _SAMPLE_CORPORA_DIR / "manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def list_sample_corpora() -> list[dict[str, Any]]:
    """Return metadata for all bundled sample corpora.

    Each entry contains ``id``, ``name``, ``description``, and counts
    for known/unknown documents.
    """
    result = []
    for entry in _load_manifest():
        result.append(
            {
                "id": entry["id"],
                "name": entry["name"],
                "description": entry["description"],
                "num_known": len(entry["known"]),
                "num_unknown": len(entry["unknown"]),
                "num_authors": len({k["author"] for k in entry["known"]}),
            }
        )
    return result


def get_sample_corpus(corpus_id: str) -> dict[str, Any]:
    """Return the full manifest entry for a sample corpus.

    Parameters
    ----------
    corpus_id:
        The corpus identifier (e.g. ``"aaac_problem_a"``).

    Raises
    ------
    KeyError
        If no corpus with the given ID exists.
    """
    for entry in _load_manifest():
        if entry["id"] == corpus_id:
            return entry
    available = [e["id"] for e in _load_manifest()]
    raise KeyError(
        f"Sample corpus {corpus_id!r} not found. " f"Available: {', '.join(available)}"
    )


def get_sample_corpus_path() -> Path:
    """Return the filesystem path to the sample corpora data directory."""
    return _SAMPLE_CORPORA_DIR

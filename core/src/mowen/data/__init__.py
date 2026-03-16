"""Data files and loaders for mowen (function word lists, etc.)."""

from __future__ import annotations

from functools import lru_cache
from importlib import resources
from pathlib import Path


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
        available = sorted(
            p.stem for p in data_dir.glob("*.txt")
        )
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

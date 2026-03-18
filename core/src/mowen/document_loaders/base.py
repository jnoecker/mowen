"""Base class for document loaders."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from mowen.types import Document


class DocumentLoader(ABC):
    """Loads a Document from a file."""

    @abstractmethod
    def load(
        self, path: Path, author: str | None = None, title: str | None = None
    ) -> Document:
        """Load a document from the given file path."""
        ...

    @staticmethod
    def supported_extensions() -> list[str]:
        """Return the file extensions this loader handles (e.g. ['.txt'])."""
        return []

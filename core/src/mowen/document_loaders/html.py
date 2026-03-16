"""HTML document loader using BeautifulSoup4."""

from __future__ import annotations

from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("Install beautifulsoup4: pip install mowen[html]")

from mowen.document_loaders.base import DocumentLoader
from mowen.exceptions import DocumentLoadError
from mowen.types import Document


class HTMLLoader(DocumentLoader):
    """Loads an HTML file as a Document."""

    @staticmethod
    def supported_extensions() -> list[str]:
        return [".html", ".htm"]

    def load(self, path: Path, author: str | None = None, title: str | None = None) -> Document:
        path = Path(path)
        if not path.exists():
            raise DocumentLoadError(f"File not found: {path}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                text = path.read_text(encoding="latin-1")
            except Exception as e:
                raise DocumentLoadError(f"Cannot decode {path}: {e}") from e
        try:
            soup = BeautifulSoup(text, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
        except DocumentLoadError:
            raise
        except Exception as e:
            raise DocumentLoadError(f"Cannot parse HTML {path}: {e}") from e
        return Document(
            text=text,
            author=author,
            title=title or path.stem,
        )

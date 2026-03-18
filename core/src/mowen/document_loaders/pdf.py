"""PDF document loader using pdfplumber."""

from __future__ import annotations

from pathlib import Path

try:
    import pdfplumber
except ImportError:
    raise ImportError("Install pdfplumber: pip install mowen[pdf]")

from mowen.document_loaders.base import DocumentLoader
from mowen.exceptions import DocumentLoadError
from mowen.types import Document


class PDFLoader(DocumentLoader):
    """Loads a PDF file as a Document."""

    @staticmethod
    def supported_extensions() -> list[str]:
        return [".pdf"]

    def load(
        self, path: Path, author: str | None = None, title: str | None = None
    ) -> Document:
        path = Path(path)
        if not path.exists():
            raise DocumentLoadError(f"File not found: {path}")
        try:
            with pdfplumber.open(path) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
            text = "\n".join(pages)
        except DocumentLoadError:
            raise
        except Exception as e:
            raise DocumentLoadError(f"Cannot read PDF {path}: {e}") from e
        return Document(
            text=text,
            author=author,
            title=title or path.stem,
        )

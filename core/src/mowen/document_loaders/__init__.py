"""Document loaders for various file formats."""

from mowen.document_loaders.base import DocumentLoader
from mowen.document_loaders.plaintext import PlainTextLoader
from mowen.exceptions import DocumentLoadError

_LOADERS: dict[str, type[DocumentLoader]] = {}

# Extensions that require optional dependencies
_OPTIONAL_EXTENSIONS: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".html": "html",
    ".htm": "html",
}


def _register_loader(loader_cls: type[DocumentLoader]) -> None:
    for ext in loader_cls.supported_extensions():
        _LOADERS[ext] = loader_cls


_register_loader(PlainTextLoader)

try:
    from mowen.document_loaders.pdf import PDFLoader

    _register_loader(PDFLoader)
except ImportError:
    pass

try:
    from mowen.document_loaders.docx import DOCXLoader

    _register_loader(DOCXLoader)
except ImportError:
    pass

try:
    from mowen.document_loaders.html import HTMLLoader

    _register_loader(HTMLLoader)
except ImportError:
    pass


def load_document(
    path: str,
    author: str | None = None,
    title: str | None = None,
) -> "Document":
    """Load a document, auto-detecting format from extension."""
    from pathlib import Path

    from mowen.types import Document

    p = Path(path)
    ext = p.suffix.lower()
    loader_cls = _LOADERS.get(ext)
    if loader_cls is None:
        if ext in _OPTIONAL_EXTENSIONS:
            dep = _OPTIONAL_EXTENSIONS[ext]
            raise DocumentLoadError(
                f"No loader registered for {ext!r} files. "
                f"Install the optional dependency: pip install 'mowen[{dep}]'"
            )
        # Truly unknown extension — try plain text
        loader_cls = PlainTextLoader
    return loader_cls().load(p, author=author, title=title)


__all__ = [
    "DocumentLoader",
    "PlainTextLoader",
    "load_document",
    *(name for name in ("PDFLoader", "DOCXLoader", "HTMLLoader") if name in globals()),
]

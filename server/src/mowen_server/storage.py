"""Local filesystem storage for uploaded documents."""

from pathlib import Path
from uuid import uuid4


class DocumentStorage:
    """Manages document files on the local filesystem.

    Each saved file is given a UUID prefix so that collisions are
    impossible even when users upload files with the same name.
    """

    def __init__(self, upload_dir: Path) -> None:
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, content: bytes) -> Path:
        """Persist *content* and return the absolute path of the new file.

        The stored filename is ``<uuid4>_<original_filename>`` so that
        the original extension is preserved while avoiding collisions.
        """
        ext = Path(filename).suffix
        stem = Path(filename).stem
        unique_name = f"{uuid4().hex}_{stem}{ext}"
        dest = self.upload_dir / unique_name
        dest.write_bytes(content)
        return dest

    def read(self, file_path: Path) -> bytes:
        """Return the raw bytes of a previously saved document."""
        return file_path.read_bytes()

    def delete(self, file_path: Path) -> None:
        """Remove a document file from disk (no-op if already gone)."""
        file_path.unlink(missing_ok=True)

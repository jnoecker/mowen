"""JGAAP experiment CSV converter.

JGAAP uses a CSV format for specifying experiments:
    filepath,author_label
    /path/to/doc1.txt,AuthorA
    /path/to/doc2.txt,AuthorB
    /path/to/unknown.txt,

Documents with an empty author field are treated as unknown.
"""

from __future__ import annotations

import csv
from pathlib import Path

from mowen.document_loaders import load_document
from mowen.types import Document


def load_jgaap_csv(
    csv_path: str | Path,
    base_dir: str | Path | None = None,
) -> tuple[list[Document], list[Document]]:
    """Load documents from a JGAAP-format CSV file.

    Parameters
    ----------
    csv_path:
        Path to the CSV file.
    base_dir:
        Optional base directory for resolving relative file paths in the CSV.
        Defaults to the parent directory of the CSV file.

    Returns
    -------
    (known_documents, unknown_documents)
    """
    csv_path = Path(csv_path)
    if base_dir is None:
        base_dir = csv_path.parent
    else:
        base_dir = Path(base_dir)

    known: list[Document] = []
    unknown: list[Document] = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not row[0].strip():
                continue
            filepath = row[0].strip()
            author = row[1].strip() if len(row) > 1 and row[1].strip() else None

            doc_path = Path(filepath)
            if not doc_path.is_absolute():
                doc_path = base_dir / doc_path

            doc = load_document(str(doc_path), author=author)

            if author:
                known.append(doc)
            else:
                unknown.append(doc)

    return known, unknown

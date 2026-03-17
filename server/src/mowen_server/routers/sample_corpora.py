"""Sample corpora listing and import endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from mowen.data import get_sample_corpus, get_sample_corpus_path, list_sample_corpora
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..db import get_db
from ..models import Corpus, CorpusDocument, Document
from ..schemas import SampleCorpusImportResponse, SampleCorpusInfo
from ..storage import DocumentStorage

router = APIRouter(prefix="/api/v1/sample-corpora", tags=["sample-corpora"])


@router.get("/", response_model=list[SampleCorpusInfo])
def list_available() -> list[SampleCorpusInfo]:
    """List all bundled sample corpora."""
    return [SampleCorpusInfo(**c) for c in list_sample_corpora()]


@router.post(
    "/{corpus_id}/import",
    response_model=SampleCorpusImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_sample_corpus(
    corpus_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SampleCorpusImportResponse:
    """Import a sample corpus, creating documents and two corpora (known + unknown)."""
    try:
        corpus_meta = get_sample_corpus(corpus_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    data_dir = get_sample_corpus_path()
    storage = DocumentStorage(settings.upload_dir)

    # Create known corpus
    known_corpus = Corpus(
        name=f"{corpus_meta['name']} \u2013 Known",
        description=f"Training documents for {corpus_meta['name']}",
    )
    db.add(known_corpus)

    # Create unknown corpus
    unknown_corpus = Corpus(
        name=f"{corpus_meta['name']} \u2013 Unknown",
        description=f"Unknown documents for {corpus_meta['name']}",
    )
    db.add(unknown_corpus)
    db.flush()  # get IDs

    # Import known documents
    for entry in corpus_meta["known"]:
        file_path = data_dir / entry["file"]
        content = file_path.read_bytes()
        filename = Path(entry["file"]).name
        saved_path = storage.save(filename, content)

        text = content.decode("utf-8", errors="replace")
        doc = Document(
            title=filename,
            author_name=entry["author"],
            file_type="txt",
            file_path=str(saved_path),
            original_filename=filename,
            char_count=len(text),
        )
        db.add(doc)
        db.flush()
        db.add(CorpusDocument(corpus_id=known_corpus.id, document_id=doc.id))

    # Import unknown documents
    for entry in corpus_meta["unknown"]:
        file_path = data_dir / entry["file"]
        content = file_path.read_bytes()
        filename = Path(entry["file"]).name
        saved_path = storage.save(filename, content)

        # Store the true author for ground-truth evaluation.
        # "NONE" in the AAAC data means the document has no known author.
        true_author = entry.get("true_author")
        if true_author == "NONE":
            true_author = None

        text = content.decode("utf-8", errors="replace")
        doc = Document(
            title=filename,
            author_name=true_author,
            file_type="txt",
            file_path=str(saved_path),
            original_filename=filename,
            char_count=len(text),
        )
        db.add(doc)
        db.flush()
        db.add(CorpusDocument(corpus_id=unknown_corpus.id, document_id=doc.id))

    db.commit()
    db.refresh(known_corpus)
    db.refresh(unknown_corpus)

    # Build response with document counts
    from ..routers.corpora import _corpus_response

    return SampleCorpusImportResponse(
        known_corpus=_corpus_response(db, known_corpus),
        unknown_corpus=_corpus_response(db, unknown_corpus),
    )

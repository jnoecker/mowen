"""Corpus management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db, get_or_404
from ..models import Corpus, CorpusDocument, Document
from ..schemas import (
    CorpusCreate,
    CorpusDocumentsRequest,
    CorpusResponse,
    CorpusUpdate,
    DocumentResponse,
)

router = APIRouter(prefix="/api/v1/corpora", tags=["corpora"])


def _corpus_response(db: Session, corpus: Corpus) -> CorpusResponse:
    """Build a CorpusResponse with a computed document_count."""
    document_count = (
        db.query(func.count(CorpusDocument.document_id))
        .filter(CorpusDocument.corpus_id == corpus.id)
        .scalar()
    ) or 0

    return CorpusResponse(
        id=corpus.id,
        name=corpus.name,
        description=corpus.description,
        document_count=document_count,
        created_at=corpus.created_at,
        updated_at=corpus.updated_at,
    )


@router.post("/", response_model=CorpusResponse, status_code=status.HTTP_201_CREATED)
def create_corpus(
    body: CorpusCreate,
    db: Session = Depends(get_db),
) -> CorpusResponse:
    """Create a new corpus."""
    corpus = Corpus(name=body.name, description=body.description)
    db.add(corpus)
    db.commit()
    db.refresh(corpus)
    return _corpus_response(db, corpus)


@router.get("/", response_model=list[CorpusResponse])
def list_corpora(
    db: Session = Depends(get_db),
    limit: int | None = Query(None, ge=1, le=10000),
    offset: int = Query(0, ge=0),
) -> list[CorpusResponse]:
    """Return corpora with document counts and optional pagination."""
    q = db.query(Corpus).offset(offset)
    if limit is not None:
        q = q.limit(limit)
    return [_corpus_response(db, c) for c in q.all()]


@router.get("/{corpus_id}", response_model=CorpusResponse)
def get_corpus(
    corpus_id: int,
    db: Session = Depends(get_db),
) -> CorpusResponse:
    """Return a single corpus by ID."""
    corpus = get_or_404(db, Corpus, corpus_id, "Corpus")
    return _corpus_response(db, corpus)


@router.patch("/{corpus_id}", response_model=CorpusResponse)
def update_corpus(
    corpus_id: int,
    body: CorpusUpdate,
    db: Session = Depends(get_db),
) -> CorpusResponse:
    """Update corpus metadata."""
    corpus = get_or_404(db, Corpus, corpus_id, "Corpus")

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(corpus, field, value)

    db.commit()
    db.refresh(corpus)
    return _corpus_response(db, corpus)


@router.delete("/{corpus_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_corpus(
    corpus_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a corpus (documents are not removed)."""
    corpus = get_or_404(db, Corpus, corpus_id, "Corpus")

    db.delete(corpus)
    db.commit()


@router.get("/{corpus_id}/documents", response_model=list[DocumentResponse])
def list_corpus_documents(
    corpus_id: int,
    db: Session = Depends(get_db),
) -> list[DocumentResponse]:
    """Return all documents belonging to a corpus."""
    get_or_404(db, Corpus, corpus_id, "Corpus")

    docs = (
        db.query(Document)
        .join(CorpusDocument, CorpusDocument.document_id == Document.id)
        .filter(CorpusDocument.corpus_id == corpus_id)
        .all()
    )
    return [DocumentResponse.model_validate(d) for d in docs]


@router.post("/{corpus_id}/documents", response_model=CorpusResponse)
def add_documents_to_corpus(
    corpus_id: int,
    body: CorpusDocumentsRequest,
    db: Session = Depends(get_db),
) -> CorpusResponse:
    """Add documents to a corpus."""
    corpus = get_or_404(db, Corpus, corpus_id, "Corpus")

    # Verify all document IDs exist
    existing_ids = {
        row[0]
        for row in db.query(Document.id)
        .filter(Document.id.in_(body.document_ids))
        .all()
    }
    missing = set(body.document_ids) - existing_ids
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Documents not found: {sorted(missing)}",
        )

    # Find which associations already exist to avoid duplicates
    already_linked = {
        row[0]
        for row in db.query(CorpusDocument.document_id)
        .filter(
            CorpusDocument.corpus_id == corpus_id,
            CorpusDocument.document_id.in_(body.document_ids),
        )
        .all()
    }

    for doc_id in body.document_ids:
        if doc_id not in already_linked:
            db.add(CorpusDocument(corpus_id=corpus_id, document_id=doc_id))

    db.commit()
    db.refresh(corpus)
    return _corpus_response(db, corpus)


@router.delete("/{corpus_id}/documents", response_model=CorpusResponse)
def remove_documents_from_corpus(
    corpus_id: int,
    body: CorpusDocumentsRequest,
    db: Session = Depends(get_db),
) -> CorpusResponse:
    """Remove documents from a corpus."""
    corpus = get_or_404(db, Corpus, corpus_id, "Corpus")

    db.query(CorpusDocument).filter(
        CorpusDocument.corpus_id == corpus_id,
        CorpusDocument.document_id.in_(body.document_ids),
    ).delete(synchronize_session="fetch")

    db.commit()
    db.refresh(corpus)
    return _corpus_response(db, corpus)

"""Document management endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, Form, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from mowen.document_loaders import load_document

from ..config import Settings, get_settings
from ..db import get_db, get_or_404
from ..models import Document
from ..schemas import DocumentResponse, DocumentUpdate
from ..storage import DocumentStorage

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile,
    title: str = Form(...),
    author_name: str | None = Form(None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Document:
    """Upload a document file and create a database record."""
    storage = DocumentStorage(settings.upload_dir)
    content = file.file.read()
    original_filename = file.filename or "untitled"
    saved_path = storage.save(original_filename, content)

    file_type = Path(original_filename).suffix.lstrip(".")

    # Extract text to compute char_count
    doc = load_document(str(saved_path), author=author_name, title=title)
    char_count = len(doc.text)

    db_document = Document(
        title=title,
        author_name=author_name,
        file_type=file_type,
        file_path=str(saved_path),
        original_filename=original_filename,
        char_count=char_count,
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


@router.get("/", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)) -> list[Document]:
    """Return all documents."""
    return db.query(Document).all()


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)) -> Document:
    """Return a single document by ID."""
    return get_or_404(db, Document, document_id, "Document")


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    body: DocumentUpdate,
    db: Session = Depends(get_db),
) -> Document:
    """Update document metadata."""
    document = get_or_404(db, Document, document_id, "Document")

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(document, field, value)

    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    """Delete a document and its backing file."""
    document = get_or_404(db, Document, document_id, "Document")

    storage = DocumentStorage(settings.upload_dir)
    storage.delete(Path(document.file_path))

    db.delete(document)
    db.commit()


@router.get("/{document_id}/text", response_class=PlainTextResponse)
def get_document_text(
    document_id: int,
    db: Session = Depends(get_db),
) -> PlainTextResponse:
    """Return the plain-text content extracted from the stored file."""
    document = get_or_404(db, Document, document_id, "Document")

    doc = load_document(
        document.file_path,
        author=document.author_name,
        title=document.title,
    )
    return PlainTextResponse(content=doc.text)

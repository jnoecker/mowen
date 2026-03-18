"""Style change detection endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from mowen.document_loaders import load_document
from mowen.pipeline import PipelineConfig
from mowen.style_change import detect_style_changes
from sqlalchemy.orm import Session

from ..db import get_db, get_or_404
from ..models import Document
from ..schemas import (
    StyleChangeBoundary,
    StyleChangeRequest,
    StyleChangeResponse,
)

router = APIRouter(prefix="/api/v1/style-change", tags=["style-change"])


@router.post("/", response_model=StyleChangeResponse)
def detect_changes(body: StyleChangeRequest, db: Session = Depends(get_db)):
    """Run style change detection on a single document."""
    db_doc = get_or_404(db, Document, body.document_id, "Document")

    doc = load_document(db_doc.file_path, author=db_doc.author_name, title=db_doc.title)

    # Build a PipelineConfig from the request fields
    config = PipelineConfig(
        event_drivers=[
            {"name": ed.name, "params": ed.params} for ed in body.event_drivers
        ],
        distance_function=(
            {"name": body.distance_function.name, "params": body.distance_function.params}
            if body.distance_function is not None
            else None
        ),
    )

    if not config.event_drivers:
        raise HTTPException(
            status_code=422,
            detail="At least one event driver is required.",
        )

    result = detect_style_changes(
        doc,
        config,
        threshold=body.threshold,
        separator=body.separator,
    )

    return StyleChangeResponse(
        document_title=db_doc.title,
        num_paragraphs=len(result.paragraphs),
        boundaries=[
            StyleChangeBoundary(
                index=p.boundary_index,
                score=p.score,
                is_change=p.is_change,
            )
            for p in result.predictions
        ],
    )

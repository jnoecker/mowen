"""Experiment management and execution endpoints."""

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from ..config import Settings, get_settings
from ..db import get_db, get_or_404
from ..models import CorpusDocument, Experiment, ExperimentCorpus, ExperimentResult
from ..runner import _make_session, experiment_runner
from ..schemas import (
    DocumentResponse,
    ExperimentConfig,
    ExperimentCreate,
    ExperimentResponse,
    ExperimentResultResponse,
    RankingEntry,
)

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


def _experiment_to_response(experiment: Experiment) -> ExperimentResponse:
    """Convert an Experiment ORM model to an ExperimentResponse schema."""
    return ExperimentResponse(
        id=experiment.id,
        name=experiment.name,
        status=experiment.status,
        config=ExperimentConfig.model_validate_json(experiment.config),
        progress=experiment.progress,
        error_message=experiment.error_message,
        created_at=experiment.created_at,
        started_at=experiment.started_at,
        completed_at=experiment.completed_at,
    )


@router.post("/", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
def create_experiment(
    body: ExperimentCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ExperimentResponse:
    """Create and submit a new experiment for execution."""
    # Reject overlapping corpus IDs
    overlap = set(body.known_corpus_ids) & set(body.unknown_corpus_ids)
    if overlap:
        raise HTTPException(
            status_code=422,
            detail=f"Corpora cannot be both known and unknown: {sorted(overlap)}",
        )

    # Check for document-level overlap
    known_doc_ids = set(
        row[0]
        for row in db.query(CorpusDocument.document_id)
        .filter(CorpusDocument.corpus_id.in_(body.known_corpus_ids))
        .all()
    )
    unknown_doc_ids = set(
        row[0]
        for row in db.query(CorpusDocument.document_id)
        .filter(CorpusDocument.corpus_id.in_(body.unknown_corpus_ids))
        .all()
    )
    doc_overlap = known_doc_ids & unknown_doc_ids
    if doc_overlap:
        raise HTTPException(
            status_code=422,
            detail=f"Documents appear in both known and unknown corpora: {sorted(doc_overlap)}",
        )

    experiment = Experiment(
        name=body.name,
        status="pending",
        config=body.config.model_dump_json(),
    )
    db.add(experiment)
    db.flush()  # Assign experiment.id

    # Create ExperimentCorpus rows for known and unknown corpora
    for corpus_id in body.known_corpus_ids:
        db.add(
            ExperimentCorpus(
                experiment_id=experiment.id,
                corpus_id=corpus_id,
                role="known",
            )
        )
    for corpus_id in body.unknown_corpus_ids:
        db.add(
            ExperimentCorpus(
                experiment_id=experiment.id,
                corpus_id=corpus_id,
                role="unknown",
            )
        )

    db.commit()
    db.refresh(experiment)

    # Submit for background execution
    experiment_runner.submit(experiment.id, settings.database_url, settings.upload_dir)

    return _experiment_to_response(experiment)


@router.get("/", response_model=list[ExperimentResponse])
def list_experiments(
    db: Session = Depends(get_db),
    limit: int | None = Query(None, ge=1, le=10000),
    offset: int = Query(0, ge=0),
) -> list[ExperimentResponse]:
    """Return experiments with optional pagination."""
    q = db.query(Experiment).offset(offset)
    if limit is not None:
        q = q.limit(limit)
    return [_experiment_to_response(e) for e in q.all()]


@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(
    experiment_id: int,
    db: Session = Depends(get_db),
) -> ExperimentResponse:
    """Return a single experiment by ID."""
    experiment = get_or_404(db, Experiment, experiment_id, "Experiment")
    return _experiment_to_response(experiment)


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experiment(
    experiment_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete an experiment and its results."""
    experiment = get_or_404(db, Experiment, experiment_id, "Experiment")

    db.delete(experiment)
    db.commit()


@router.get("/{experiment_id}/results", response_model=list[ExperimentResultResponse])
def get_experiment_results(
    experiment_id: int,
    db: Session = Depends(get_db),
) -> list[ExperimentResultResponse]:
    """Return results for a completed experiment."""
    experiment = get_or_404(db, Experiment, experiment_id, "Experiment")
    if experiment.status != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"Experiment is not completed (status={experiment.status!r})",
        )

    results = (
        db.query(ExperimentResult)
        .filter(ExperimentResult.experiment_id == experiment_id)
        .all()
    )

    lower_is_better = bool(experiment.lower_is_better)

    response: list[ExperimentResultResponse] = []
    for result in results:
        rankings_data = json.loads(result.rankings)
        response.append(
            ExperimentResultResponse(
                unknown_document=DocumentResponse.model_validate(
                    result.unknown_document, from_attributes=True
                ),
                rankings=[RankingEntry(**r) for r in rankings_data],
                lower_is_better=lower_is_better,
            )
        )

    return response


@router.get("/{experiment_id}/progress")
def get_experiment_progress(
    experiment_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """SSE endpoint for real-time experiment progress updates."""
    # Verify the experiment exists before opening the stream
    get_or_404(db, Experiment, experiment_id, "Experiment")

    return StreamingResponse(
        _progress_stream(experiment_id, settings.database_url),
        media_type="text/event-stream",
    )


async def _progress_stream(experiment_id: int, db_url: str):
    """Async generator that yields SSE events with experiment progress."""
    session, cleanup = _make_session(db_url)
    try:
        while True:
            exp = session.get(Experiment, experiment_id)
            session.refresh(exp)
            data = json.dumps({"progress": exp.progress, "status": exp.status})
            yield f"data: {data}\n\n"
            if exp.status in ("completed", "failed"):
                break
            await asyncio.sleep(1)
    finally:
        cleanup()

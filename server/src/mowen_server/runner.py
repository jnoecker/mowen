"""In-process experiment runner using background threads."""

import json
import logging
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger("mowen_server.runner")

from mowen.document_loaders import load_document
from mowen.pipeline import Pipeline, PipelineConfig
from mowen.types import Document as MowenDocument
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .models import (
    CorpusDocument,
    Experiment,
    ExperimentResult,
)
from .models import Document as DBDocument


def _make_session(db_url: str) -> tuple[Session, Callable[[], None]]:
    """Create a new engine+session and return (session, cleanup_fn)."""
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(db_url, connect_args=connect_args)
    session = Session(engine)

    def cleanup() -> None:
        session.close()
        engine.dispose()

    return session, cleanup


def _load_corpus_docs(
    session: Session, corpus_ids: list[int]
) -> tuple[list[MowenDocument], list[int]]:
    """Load documents from corpora, returning (mowen_docs, db_doc_ids)."""
    docs: list[MowenDocument] = []
    doc_ids: list[int] = []
    seen: set[int] = set()
    for cd in (
        session.query(CorpusDocument)
        .filter(CorpusDocument.corpus_id.in_(corpus_ids))
        .all()
    ):
        if cd.document_id in seen:
            continue
        seen.add(cd.document_id)
        db_doc = session.get(DBDocument, cd.document_id)
        if db_doc is None:
            continue
        docs.append(
            load_document(db_doc.file_path, author=db_doc.author_name, title=db_doc.title)
        )
        doc_ids.append(db_doc.id)
    return docs, doc_ids


def execute_experiment(experiment_id: int, session: Session) -> None:
    """Run the experiment pipeline within the given session.

    This is the core execution logic, separated from threading concerns
    so it can be called synchronously in tests or from a background thread.
    """
    experiment = session.get(Experiment, experiment_id)
    if experiment is None:
        return

    experiment.status = "running"
    experiment.started_at = datetime.now(UTC)
    session.commit()

    # Load config
    config_dict = json.loads(experiment.config)

    # Collect corpus IDs by role
    known_corpus_ids = [
        ec.corpus_id for ec in experiment.corpora if ec.role == "known"
    ]
    unknown_corpus_ids = [
        ec.corpus_id for ec in experiment.corpora if ec.role == "unknown"
    ]

    # Load documents
    known_docs, _ = _load_corpus_docs(session, known_corpus_ids)
    unknown_docs, unknown_doc_id_map = _load_corpus_docs(session, unknown_corpus_ids)

    # Build pipeline
    pipeline_config = PipelineConfig(**config_dict)

    last_committed_progress = 0.0

    def _progress_callback(fraction: float, message: str) -> None:
        nonlocal last_committed_progress
        if fraction - last_committed_progress >= 0.05 or fraction >= 1.0:
            experiment.progress = fraction
            session.commit()
            last_committed_progress = fraction

    results = Pipeline(
        config=pipeline_config, progress_callback=_progress_callback
    ).execute(known_docs, unknown_docs)

    # Store results
    for i, result in enumerate(results):
        rankings_json = json.dumps(
            [{"author": a.author, "score": a.score} for a in result.rankings]
        )
        session.add(
            ExperimentResult(
                experiment_id=experiment_id,
                unknown_doc_id=unknown_doc_id_map[i],
                rankings=rankings_json,
            )
        )

    if results:
        experiment.lower_is_better = int(results[0].lower_is_better)
        experiment.verification_threshold = results[0].verification_threshold
    experiment.status = "completed"
    experiment.completed_at = datetime.now(UTC)
    experiment.progress = 1.0
    session.commit()


class ExperimentRunner:
    """Runs experiments in background threads."""

    def __init__(self) -> None:
        self._threads: dict[int, threading.Thread] = {}

    def submit(self, experiment_id: int, db_url: str, upload_dir: Path) -> None:
        """Start a background thread to run the experiment."""
        thread = threading.Thread(
            target=self._run_in_thread,
            args=(experiment_id, db_url),
            daemon=True,
        )
        self._threads[experiment_id] = thread
        thread.start()

    def wait(self, experiment_id: int, timeout: float = 30.0) -> None:
        """Wait for an experiment thread to finish (for testing)."""
        thread = self._threads.get(experiment_id)
        if thread is not None:
            thread.join(timeout=timeout)

    @staticmethod
    def _run_in_thread(experiment_id: int, db_url: str) -> None:
        """Thread target: creates its own session and runs the experiment."""
        session, cleanup = _make_session(db_url)
        try:
            execute_experiment(experiment_id, session)
        except Exception as e:
            logger.exception("Experiment %d failed", experiment_id)
            try:
                session.rollback()
                experiment = session.get(Experiment, experiment_id)
                if experiment:
                    experiment.status = "failed"
                    experiment.error_message = str(e)
                    experiment.completed_at = datetime.now(UTC)
                    session.commit()
            except Exception:
                logger.exception(
                    "Failed to record error status for experiment %d",
                    experiment_id,
                )
        finally:
            cleanup()


# Module-level singleton
experiment_runner = ExperimentRunner()

"""In-process experiment runner using background threads."""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from mowen.document_loaders import load_document
from mowen.pipeline import Pipeline, PipelineConfig
from mowen.types import Document as MowenDocument

from .models import (
    CorpusDocument,
    Experiment,
    ExperimentCorpus,
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


def execute_experiment(experiment_id: int, session: Session) -> None:
    """Run the experiment pipeline within the given session.

    This is the core execution logic, separated from threading concerns
    so it can be called synchronously in tests or from a background thread.
    """
    experiment = session.get(Experiment, experiment_id)
    if experiment is None:
        return

    experiment.status = "running"
    experiment.started_at = datetime.utcnow()
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
    known_docs: list[MowenDocument] = []
    unknown_docs: list[MowenDocument] = []
    unknown_doc_id_map: list[int] = []

    seen_known: set[int] = set()
    for cd in (
        session.query(CorpusDocument)
        .filter(CorpusDocument.corpus_id.in_(known_corpus_ids))
        .all()
    ):
        if cd.document_id in seen_known:
            continue
        seen_known.add(cd.document_id)
        db_doc = session.get(DBDocument, cd.document_id)
        if db_doc is None:
            continue
        known_docs.append(
            load_document(db_doc.file_path, author=db_doc.author_name, title=db_doc.title)
        )

    seen_unknown: set[int] = set()
    for cd in (
        session.query(CorpusDocument)
        .filter(CorpusDocument.corpus_id.in_(unknown_corpus_ids))
        .all()
    ):
        if cd.document_id in seen_unknown:
            continue
        seen_unknown.add(cd.document_id)
        db_doc = session.get(DBDocument, cd.document_id)
        if db_doc is None:
            continue
        unknown_docs.append(
            load_document(db_doc.file_path, author=db_doc.author_name, title=db_doc.title)
        )
        unknown_doc_id_map.append(db_doc.id)

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

    experiment.status = "completed"
    experiment.completed_at = datetime.utcnow()
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
            try:
                session.rollback()
                experiment = session.get(Experiment, experiment_id)
                if experiment:
                    experiment.status = "failed"
                    experiment.error_message = str(e)
                    experiment.completed_at = datetime.utcnow()
                    session.commit()
            except Exception:
                pass
        finally:
            cleanup()


# Module-level singleton
experiment_runner = ExperimentRunner()

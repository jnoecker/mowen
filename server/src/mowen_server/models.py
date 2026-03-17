"""SQLAlchemy ORM models for the mowen database."""

from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    author_name = Column(String, nullable=True)
    file_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    char_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    corpora = relationship(
        "Corpus", secondary="corpus_documents", back_populates="documents"
    )


class Corpus(Base):
    __tablename__ = "corpora"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    documents = relationship(
        "Document", secondary="corpus_documents", back_populates="corpora"
    )
    experiments = relationship(
        "ExperimentCorpus", back_populates="corpus",
        cascade="all, delete-orphan", passive_deletes=True,
    )


class CorpusDocument(Base):
    __tablename__ = "corpus_documents"

    corpus_id = Column(
        Integer, ForeignKey("corpora.id", ondelete="CASCADE"), primary_key=True
    )
    document_id = Column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    config = Column(Text, nullable=False)  # JSON stored as Text
    progress = Column(Float, nullable=False, default=0.0)
    error_message = Column(String, nullable=True)
    lower_is_better = Column(Integer, nullable=False, default=1)  # boolean as int
    verification_threshold = Column(Float, nullable=True)  # null for non-verification methods
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    corpora = relationship(
        "ExperimentCorpus", back_populates="experiment", cascade="all, delete-orphan"
    )
    results = relationship(
        "ExperimentResult", back_populates="experiment", cascade="all, delete-orphan"
    )


class ExperimentCorpus(Base):
    __tablename__ = "experiment_corpora"

    experiment_id = Column(
        Integer, ForeignKey("experiments.id", ondelete="CASCADE"), primary_key=True
    )
    corpus_id = Column(
        Integer, ForeignKey("corpora.id", ondelete="CASCADE"), primary_key=True
    )
    role = Column(String, nullable=False)  # "known" or "unknown"

    experiment = relationship("Experiment", back_populates="corpora")
    corpus = relationship("Corpus", back_populates="experiments")


class ExperimentResult(Base):
    __tablename__ = "experiment_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(
        Integer, ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False
    )
    unknown_doc_id = Column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    rankings = Column(Text, nullable=False)  # JSON stored as Text
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    experiment = relationship("Experiment", back_populates="results")
    unknown_document = relationship("Document")

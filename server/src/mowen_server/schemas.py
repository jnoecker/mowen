"""Pydantic request / response schemas for the mowen API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

class DocumentCreate(BaseModel):
    """Metadata submitted alongside a file upload."""

    title: str
    author_name: str | None = None


class DocumentUpdate(BaseModel):
    """Partial update payload for a document."""

    title: str | None = None
    author_name: str | None = None


class DocumentResponse(BaseModel):
    """Public representation of a stored document."""

    id: int
    title: str
    author_name: str | None
    file_type: str
    original_filename: str
    char_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Corpora
# ---------------------------------------------------------------------------

class CorpusCreate(BaseModel):
    name: str
    description: str = ""


class CorpusUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CorpusResponse(BaseModel):
    id: int
    name: str
    description: str
    document_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CorpusDocumentsRequest(BaseModel):
    """Body for adding / removing documents in a corpus."""

    document_ids: list[int]


# ---------------------------------------------------------------------------
# Sample corpora
# ---------------------------------------------------------------------------

class SampleCorpusInfo(BaseModel):
    """Metadata for a bundled sample corpus."""

    id: str
    name: str
    description: str
    num_known: int
    num_unknown: int
    num_authors: int


class SampleCorpusImportResponse(BaseModel):
    """Result of importing a sample corpus."""

    known_corpus: CorpusResponse
    unknown_corpus: CorpusResponse


# ---------------------------------------------------------------------------
# Pipeline components
# ---------------------------------------------------------------------------

class ParamInfo(BaseModel):
    """Describes a single tuneable parameter of a pipeline component."""

    name: str
    type: str
    default: str | int | float | bool | None = None
    description: str = ""
    min_value: float | None = None
    max_value: float | None = None
    choices: list[str] | None = None


class ComponentInfo(BaseModel):
    """Public description of a registered pipeline component."""

    name: str
    display_name: str
    description: str
    params: list[ParamInfo] | None = None
    numeric: bool | None = None


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------

class ComponentSpec(BaseModel):
    """Reference to a pipeline component together with param overrides."""

    name: str
    params: dict[str, str | int | float | bool] = {}


class ExperimentConfig(BaseModel):
    """Full pipeline specification stored with an experiment."""

    canonicizers: list[ComponentSpec] = []
    event_drivers: list[ComponentSpec] = []
    event_cullers: list[ComponentSpec] = []
    distance_function: ComponentSpec | None = None
    analysis_method: ComponentSpec


class ExperimentCreate(BaseModel):
    name: str
    config: ExperimentConfig
    known_corpus_ids: list[int]
    unknown_corpus_ids: list[int]


class ExperimentResponse(BaseModel):
    id: int
    name: str
    status: str
    config: ExperimentConfig
    progress: float
    error_message: str | None
    known_corpus_ids: list[int] = []
    unknown_corpus_ids: list[int] = []
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class RankingEntry(BaseModel):
    """A single author ranking within an experiment result."""

    author: str
    score: float


class ExperimentResultResponse(BaseModel):
    unknown_document: DocumentResponse
    rankings: list[RankingEntry]
    lower_is_better: bool = True
    verification_threshold: float | None = None

    model_config = ConfigDict(from_attributes=True)

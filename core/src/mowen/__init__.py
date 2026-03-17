"""mowen — authorship attribution toolkit."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mowen")
except PackageNotFoundError:
    __version__ = "1.0.0"  # fallback for editable installs

from mowen.document_loaders import load_document
from mowen.evaluation import (
    AuthorMetrics,
    EvaluationResult,
    FoldResult,
    Prediction,
    k_fold,
    leave_one_out,
    write_results_csv,
)
from mowen.pipeline import ComponentSpec, Pipeline, PipelineConfig
from mowen.tokenizers import Tokenizer, tokenizer_registry
from mowen.types import (
    Attribution,
    Document,
    Event,
    EventSet,
    Histogram,
    NumericEventSet,
    PipelineResult,
)

__all__ = [
    "Attribution",
    "AuthorMetrics",
    "ComponentSpec",
    "Document",
    "EvaluationResult",
    "Event",
    "EventSet",
    "FoldResult",
    "Histogram",
    "NumericEventSet",
    "Pipeline",
    "PipelineConfig",
    "PipelineResult",
    "Prediction",
    "k_fold",
    "leave_one_out",
    "load_document",
    "Tokenizer",
    "tokenizer_registry",
    "write_results_csv",
]

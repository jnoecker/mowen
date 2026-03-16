"""mowen — authorship attribution toolkit."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mowen")
except PackageNotFoundError:
    __version__ = "0.1.0"  # fallback for editable installs

from mowen.pipeline import Pipeline, PipelineConfig, ComponentSpec
from mowen.types import Attribution, Document, Event, EventSet, Histogram, NumericEventSet, PipelineResult
from mowen.document_loaders import load_document

__all__ = [
    "Attribution",
    "ComponentSpec",
    "Document",
    "Event",
    "EventSet",
    "Histogram",
    "Pipeline",
    "PipelineConfig",
    "PipelineResult",
    "load_document",
]

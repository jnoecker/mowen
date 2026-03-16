"""mowen — authorship attribution toolkit."""

__version__ = "0.1.0"

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

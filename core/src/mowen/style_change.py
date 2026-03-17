"""Style change detection for multi-author documents.

Detects paragraph-level authorship changes within a document by
measuring stylistic distance between adjacent segments.
"""

from __future__ import annotations

from dataclasses import dataclass

from mowen.canonicizers import canonicizer_registry
from mowen.distance_functions import distance_function_registry
from mowen.event_drivers import event_driver_registry
from mowen.pipeline import ComponentSpec, PipelineConfig
from mowen.types import Document


@dataclass(frozen=True, slots=True)
class StyleChangePrediction:
    """Prediction at one paragraph boundary."""

    boundary_index: int
    score: float  # 0-1, higher = more likely style change
    is_change: bool


@dataclass
class StyleChangeResult:
    """Result of style change detection on one document."""

    document: Document
    paragraphs: list[str]
    predictions: list[StyleChangePrediction]


def detect_style_changes(
    document: Document,
    config: PipelineConfig,
    *,
    threshold: float = 0.5,
    separator: str = "\n\n",
) -> StyleChangeResult:
    """Detect authorship changes at paragraph boundaries.

    Parameters
    ----------
    document:
        The document to analyze.
    config:
        Pipeline configuration specifying event drivers and distance
        function.  Canonicizers are applied to each paragraph.
    threshold:
        Normalized distance above which a boundary is flagged as a
        style change (0-1).
    separator:
        String used to split text into paragraphs.

    Returns
    -------
    StyleChangeResult
        One prediction per paragraph boundary (n-1 for n paragraphs).
    """
    paragraphs = [p.strip() for p in document.text.split(separator) if p.strip()]

    if len(paragraphs) < 2:
        return StyleChangeResult(
            document=document,
            paragraphs=paragraphs,
            predictions=[],
        )

    # Instantiate components
    canonicizers = [
        canonicizer_registry.create(s.name, s.params)
        for s in config.canonicizers
    ]
    event_drivers = [
        event_driver_registry.create(s.name, s.params)
        for s in config.event_drivers
    ]

    df_spec = config.distance_function
    if df_spec is None:
        df_spec = ComponentSpec(name="cosine")
    distance_fn = distance_function_registry.create(df_spec.name, df_spec.params)

    # Build histogram for each paragraph
    histograms = []
    for para in paragraphs:
        # Canonicize
        text = para
        for canon in canonicizers:
            text = canon.process(text)

        # Extract events and build histogram
        from mowen.types import EventSet
        combined = EventSet()
        for driver in event_drivers:
            combined.extend(driver.create_event_set(text))
        histograms.append(combined.to_histogram())

    # Compute distances between adjacent paragraphs
    distances: list[float] = []
    for i in range(len(histograms) - 1):
        dist = distance_fn.distance(histograms[i], histograms[i + 1])
        distances.append(dist)

    # Normalize to [0, 1]
    if distances:
        min_d = min(distances)
        max_d = max(distances)
        rng = max_d - min_d
        if rng > 0:
            normalized = [(d - min_d) / rng for d in distances]
        else:
            normalized = [0.5] * len(distances)
    else:
        normalized = []

    predictions = [
        StyleChangePrediction(
            boundary_index=i,
            score=normalized[i],
            is_change=normalized[i] >= threshold,
        )
        for i in range(len(normalized))
    ]

    return StyleChangeResult(
        document=document,
        paragraphs=paragraphs,
        predictions=predictions,
    )

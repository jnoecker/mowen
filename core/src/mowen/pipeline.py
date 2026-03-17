"""Pipeline orchestrator — runs the full attribution workflow."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger("mowen.pipeline")

from mowen.analysis_methods import AnalysisMethod, NeighborAnalysisMethod, analysis_method_registry
from mowen.canonicizers import canonicizer_registry
from mowen.distance_functions import distance_function_registry
from mowen.event_cullers import event_culler_registry
from mowen.event_drivers import event_driver_registry
from mowen.exceptions import PipelineError
from mowen.types import Attribution, Document, EventSet, Histogram, NumericEventSet, PipelineResult


@dataclass
class ComponentSpec:
    """Specifies a component by registry name and optional parameters."""

    name: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    """Full specification of an attribution pipeline."""

    canonicizers: list[ComponentSpec | dict[str, Any]] = field(default_factory=list)
    event_drivers: list[ComponentSpec | dict[str, Any]] = field(default_factory=list)
    event_cullers: list[ComponentSpec | dict[str, Any]] = field(default_factory=list)
    distance_function: ComponentSpec | dict[str, Any] | None = None
    analysis_method: ComponentSpec | dict[str, Any] = field(
        default_factory=lambda: ComponentSpec(name="nearest_neighbor")
    )

    def __post_init__(self) -> None:
        """Normalize all component specs from dict to ComponentSpec at construction."""
        self.canonicizers = [self._normalize(c) for c in self.canonicizers]
        self.event_drivers = [self._normalize(d) for d in self.event_drivers]
        self.event_cullers = [self._normalize(c) for c in self.event_cullers]
        if self.distance_function is not None:
            self.distance_function = self._normalize(self.distance_function)
        self.analysis_method = self._normalize(self.analysis_method)

    @staticmethod
    def _normalize(spec: ComponentSpec | dict[str, Any]) -> ComponentSpec:
        if isinstance(spec, ComponentSpec):
            return spec
        return ComponentSpec(name=spec["name"], params=spec.get("params", {}))


ProgressCallback = Callable[[float, str], None]


class Pipeline:
    """Executes the full canonicize → extract → cull → analyze pipeline.

    Supports two execution paths:

    * **Discrete path** (standard event drivers): text → events → cull →
      histograms → distance/analysis.
    * **Numeric path** (transformer embeddings): text → dense vectors →
      sklearn classifier directly (cullers, distance functions skipped).
    """

    def __init__(
        self,
        config: PipelineConfig,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self.config = config
        self._progress = progress_callback

    def _report(self, fraction: float, message: str) -> None:
        if self._progress:
            self._progress(fraction, message)

    def execute(
        self,
        known_documents: list[Document],
        unknown_documents: list[Document],
    ) -> list[PipelineResult]:
        """Run the full pipeline, returning results for each unknown document."""
        if not known_documents:
            raise PipelineError("At least one known document is required")
        if not unknown_documents:
            raise PipelineError("At least one unknown document is required")
        if not self.config.event_drivers:
            raise PipelineError("At least one event driver is required")
        if self.config.analysis_method is None:
            raise PipelineError("An analysis method is required")

        # --- 1. Instantiate components ---
        self._report(0.0, "Initializing components")

        canonicizers = [
            canonicizer_registry.create(s.name, s.params)
            for s in self.config.canonicizers
        ]
        event_drivers = [
            event_driver_registry.create(s.name, s.params)
            for s in self.config.event_drivers
        ]
        event_cullers = [
            event_culler_registry.create(s.name, s.params)
            for s in self.config.event_cullers
        ]

        am_spec = self.config.analysis_method
        analysis_method: AnalysisMethod = analysis_method_registry.create(
            am_spec.name, am_spec.params
        )

        distance_fn = None
        if self.config.distance_function is not None:
            df_spec = self.config.distance_function
            distance_fn = distance_function_registry.create(df_spec.name, df_spec.params)

        if isinstance(analysis_method, NeighborAnalysisMethod):
            if distance_fn is None:
                raise PipelineError(
                    f"Analysis method {am_spec.name!r} requires a distance function"
                )
            analysis_method.distance_function = distance_fn

        # --- 2. Canonicize ---
        self._report(0.1, "Canonicizing documents")
        all_docs = known_documents + unknown_documents
        canonicized_texts: dict[int, str] = {}
        for idx, doc in enumerate(all_docs):
            text = doc.text
            for canon in canonicizers:
                text = canon.process(text)
            canonicized_texts[idx] = text
            if not text.strip():
                logger.warning(
                    "Document %r has empty text after canonicization",
                    all_docs[idx].title,
                )

        # --- 3. Extract events ---
        self._report(0.3, "Extracting events")
        doc_features: dict[int, EventSet | NumericEventSet] = {}
        for idx in range(len(all_docs)):
            first_result = event_drivers[0].create_event_set(canonicized_texts[idx])

            if isinstance(first_result, NumericEventSet):
                # Numeric path: concatenate embedding vectors from all drivers
                combined = list(first_result)
                for driver in event_drivers[1:]:
                    es = driver.create_event_set(canonicized_texts[idx])
                    if not isinstance(es, NumericEventSet):
                        raise PipelineError(
                            "Cannot mix numeric and discrete event drivers. "
                            "Use transformer_embeddings alone or with other embedding drivers."
                        )
                    combined.extend(es)
                doc_features[idx] = NumericEventSet(combined)
            else:
                # Discrete path: concatenate event sets
                combined_events = EventSet(first_result)
                for driver in event_drivers[1:]:
                    es = driver.create_event_set(canonicized_texts[idx])
                    if isinstance(es, NumericEventSet):
                        raise PipelineError(
                            "Cannot mix numeric and discrete event drivers. "
                            "Use transformer_embeddings alone or with other embedding drivers."
                        )
                    combined_events.extend(es)
                doc_features[idx] = combined_events

        # Detect which path we're on
        numeric_mode = isinstance(doc_features[0], NumericEventSet)
        n_known = len(known_documents)

        if numeric_mode:
            # --- Numeric path: skip cullers and histograms ---
            if isinstance(analysis_method, NeighborAnalysisMethod):
                raise PipelineError(
                    f"Analysis method {am_spec.name!r} uses a distance function and "
                    f"is not compatible with transformer embeddings. "
                    f"Use an sklearn-based method instead "
                    f"(e.g. 'svm', 'knn', 'lda', 'logistic_regression', 'random_forest')."
                )
            self._report(0.6, "Preparing feature vectors")

            # Pass NumericEventSets directly as "histograms" — the sklearn
            # analysis methods detect this and use them as raw feature vectors.
            known_data: list[tuple[Document, Histogram]] = [
                (all_docs[i], doc_features[i])  # type: ignore[misc]
                for i in range(n_known)
            ]

            self._report(0.7, "Training analysis method")
            analysis_method.train(known_data)

            self._report(0.8, "Analyzing unknown documents")
            results: list[PipelineResult] = []
            for i, doc in enumerate(unknown_documents):
                idx = n_known + i
                rankings = analysis_method.analyze(doc_features[idx])  # type: ignore[arg-type]
                results.append(PipelineResult(
                    unknown_document=doc,
                    rankings=rankings,
                    lower_is_better=analysis_method.lower_is_better,
                ))
                progress = 0.8 + 0.2 * (i + 1) / len(unknown_documents)
                self._report(progress, f"Analyzed {i + 1}/{len(unknown_documents)}")

            return results

        # --- Discrete path: cull → histogram → analyze ---

        # Narrow type for discrete path
        doc_event_sets: dict[int, EventSet] = doc_features  # type: ignore[assignment]

        # --- 4. Cull events ---
        self._report(0.5, "Culling events")
        if event_cullers:
            # Only derive statistics from known documents to prevent data leakage.
            known_event_sets = [doc_event_sets[i] for i in range(n_known)]
            for culler in event_cullers:
                culler.init(known_event_sets)
                doc_event_sets = {
                    idx: culler.cull(es) for idx, es in doc_event_sets.items()
                }

        # --- 5. Build histograms ---
        self._report(0.6, "Building histograms")
        doc_histograms: dict[int, Histogram] = {
            idx: es.to_histogram() for idx, es in doc_event_sets.items()
        }

        # --- 6. Train analysis method ---
        self._report(0.7, "Training analysis method")
        known_data_discrete = [(all_docs[i], doc_histograms[i]) for i in range(n_known)]
        analysis_method.train(known_data_discrete)

        # --- 7. Analyze unknown documents ---
        self._report(0.8, "Analyzing unknown documents")
        results = []
        for i, doc in enumerate(unknown_documents):
            idx = n_known + i
            rankings: list[Attribution] = analysis_method.analyze(doc_histograms[idx])
            results.append(PipelineResult(
                unknown_document=doc,
                rankings=rankings,
                lower_is_better=analysis_method.lower_is_better,
            ))
            progress = 0.8 + 0.2 * (i + 1) / len(unknown_documents)
            self._report(progress, f"Analyzed {i + 1}/{len(unknown_documents)}")

        return results

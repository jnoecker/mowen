"""Cross-validation and evaluation metrics for authorship attribution."""

from __future__ import annotations

import csv
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO

from mowen.exceptions import EvaluationError
from mowen.pipeline import Pipeline, PipelineConfig, ProgressCallback
from mowen.types import Document

logger = logging.getLogger("mowen.evaluation")


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Prediction:
    """A single prediction: true author vs. predicted author."""

    document_title: str
    true_author: str
    predicted_author: str
    scores: tuple[tuple[str, float], ...]  # full ranking as ((author, score), ...)


@dataclass
class FoldResult:
    """Results from a single cross-validation fold."""

    fold_index: int
    predictions: list[Prediction]

    @property
    def correct(self) -> int:
        return sum(1 for p in self.predictions if p.true_author == p.predicted_author)

    @property
    def total(self) -> int:
        return len(self.predictions)

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total > 0 else 0.0


@dataclass(frozen=True, slots=True)
class AuthorMetrics:
    """Precision, recall, and F1 for a single author."""

    author: str
    precision: float
    recall: float
    f1: float
    support: int  # number of true instances


@dataclass
class EvaluationResult:
    """Aggregate evaluation results across all folds."""

    fold_results: list[FoldResult]
    accuracy: float
    per_author: list[AuthorMetrics]
    macro_precision: float
    macro_recall: float
    macro_f1: float
    confusion_matrix: dict[str, dict[str, int]]


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------


def _compute_metrics(fold_results: list[FoldResult]) -> EvaluationResult:
    """Compute aggregate metrics from fold results."""
    # Flatten predictions
    all_preds = [p for fr in fold_results for p in fr.predictions]
    total = len(all_preds)
    correct = sum(1 for p in all_preds if p.true_author == p.predicted_author)
    accuracy = correct / total if total > 0 else 0.0

    # Confusion matrix
    authors = sorted({p.true_author for p in all_preds} | {p.predicted_author for p in all_preds})
    cm: dict[str, dict[str, int]] = {a: {b: 0 for b in authors} for a in authors}
    for p in all_preds:
        cm[p.true_author][p.predicted_author] += 1

    # Per-author precision / recall / F1
    per_author: list[AuthorMetrics] = []
    for author in authors:
        tp = cm[author][author]
        fp = sum(cm[other][author] for other in authors if other != author)
        fn = sum(cm[author][other] for other in authors if other != author)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        per_author.append(AuthorMetrics(
            author=author, precision=precision, recall=recall,
            f1=f1, support=tp + fn,
        ))

    n_authors = len(per_author)
    macro_p = sum(a.precision for a in per_author) / n_authors if n_authors else 0.0
    macro_r = sum(a.recall for a in per_author) / n_authors if n_authors else 0.0
    macro_f1 = sum(a.f1 for a in per_author) / n_authors if n_authors else 0.0

    return EvaluationResult(
        fold_results=fold_results,
        accuracy=accuracy,
        per_author=per_author,
        macro_precision=macro_p,
        macro_recall=macro_r,
        macro_f1=macro_f1,
        confusion_matrix=cm,
    )


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------


def _validate_documents(documents: list[Document], min_docs: int = 2) -> None:
    """Check documents are suitable for evaluation."""
    if len(documents) < min_docs:
        raise EvaluationError(
            f"At least {min_docs} documents are required, got {len(documents)}"
        )
    missing = [d.title or f"(index {i})" for i, d in enumerate(documents) if not d.author]
    if missing:
        raise EvaluationError(
            f"All documents must have an author. Missing author on: {', '.join(missing[:5])}"
        )
    authors = {d.author for d in documents}
    if len(authors) < 2:
        raise EvaluationError(
            f"At least 2 distinct authors are required, got {len(authors)}: {authors}"
        )


def _make_prediction(result, true_author: str) -> Prediction:
    """Build a Prediction from a PipelineResult."""
    return Prediction(
        document_title=result.unknown_document.title,
        true_author=true_author,
        predicted_author=result.top_author or "",
        scores=tuple((a.author, a.score) for a in result.rankings),
    )


# ---------------------------------------------------------------------------
# Leave-one-out cross-validation
# ---------------------------------------------------------------------------


def leave_one_out(
    documents: list[Document],
    config: PipelineConfig,
    progress_callback: ProgressCallback | None = None,
) -> EvaluationResult:
    """Leave-one-out cross-validation.

    Each document is held out once as unknown while the rest serve as
    training data.  All documents must have a non-None ``author``.

    Parameters
    ----------
    documents:
        Known-author documents (>= 2, >= 2 distinct authors).
    config:
        Pipeline configuration to use for each fold.
    progress_callback:
        Optional ``(fraction, message)`` callback.

    Returns
    -------
    EvaluationResult
        One fold per document.
    """
    _validate_documents(documents)

    fold_results: list[FoldResult] = []
    n = len(documents)

    for i, held_out in enumerate(documents):
        train = documents[:i] + documents[i + 1:]
        # Skip fold if training set has < 2 authors
        train_authors = {d.author for d in train}
        if len(train_authors) < 2:
            logger.warning(
                "Fold %d skipped: training set has only 1 author (%s)",
                i, train_authors,
            )
            continue

        if progress_callback:
            progress_callback(i / n, f"LOO fold {i + 1}/{n}")

        results = Pipeline(config).execute(train, [held_out])
        pred = _make_prediction(results[0], held_out.author or "")
        fold_results.append(FoldResult(fold_index=i, predictions=[pred]))

    if progress_callback:
        progress_callback(1.0, "Evaluation complete")

    return _compute_metrics(fold_results)


# ---------------------------------------------------------------------------
# K-fold cross-validation
# ---------------------------------------------------------------------------


def k_fold(
    documents: list[Document],
    config: PipelineConfig,
    k: int = 10,
    *,
    shuffle: bool = True,
    random_seed: int | None = None,
    progress_callback: ProgressCallback | None = None,
) -> EvaluationResult:
    """K-fold cross-validation.

    Parameters
    ----------
    documents:
        Known-author documents (>= k, >= 2 distinct authors).
    config:
        Pipeline configuration to use for each fold.
    k:
        Number of folds (default 10).  Clamped to ``len(documents)`` if
        larger.
    shuffle:
        Shuffle documents before splitting (default True).
    random_seed:
        Seed for reproducible shuffling.
    progress_callback:
        Optional ``(fraction, message)`` callback.

    Returns
    -------
    EvaluationResult
        One FoldResult per fold.
    """
    if k < 2:
        raise EvaluationError(f"k must be >= 2, got {k}")
    _validate_documents(documents)

    docs = list(documents)
    if k > len(docs):
        logger.warning("k=%d exceeds document count %d; clamping to LOO", k, len(docs))
        k = len(docs)

    if shuffle:
        rng = random.Random(random_seed)
        rng.shuffle(docs)

    # Build folds
    folds: list[list[Document]] = []
    n = len(docs)
    for i in range(k):
        start = i * n // k
        end = (i + 1) * n // k
        folds.append(docs[start:end])

    fold_results: list[FoldResult] = []
    for i, test_fold in enumerate(folds):
        train = [d for j, fold in enumerate(folds) for d in fold if j != i]
        train_authors = {d.author for d in train}
        if len(train_authors) < 2:
            logger.warning(
                "Fold %d skipped: training set has only 1 author", i,
            )
            continue

        if progress_callback:
            progress_callback(i / k, f"Fold {i + 1}/{k}")

        results = Pipeline(config).execute(train, test_fold)
        preds = [
            _make_prediction(r, test_fold[j].author or "")
            for j, r in enumerate(results)
        ]
        fold_results.append(FoldResult(fold_index=i, predictions=preds))

    if progress_callback:
        progress_callback(1.0, "Evaluation complete")

    return _compute_metrics(fold_results)


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


def write_results_csv(
    result: EvaluationResult,
    output: str | Path | IO[str],
) -> None:
    """Write evaluation results to a CSV file.

    Sections: summary, per-author metrics, confusion matrix, predictions.
    """
    should_close = False
    if isinstance(output, (str, Path)):
        output = open(output, "w", newline="")
        should_close = True

    try:
        w = csv.writer(output)

        # Summary
        w.writerow(["section", "metric", "value"])
        w.writerow(["summary", "accuracy", f"{result.accuracy:.6f}"])
        w.writerow(["summary", "macro_precision", f"{result.macro_precision:.6f}"])
        w.writerow(["summary", "macro_recall", f"{result.macro_recall:.6f}"])
        w.writerow(["summary", "macro_f1", f"{result.macro_f1:.6f}"])
        w.writerow([])

        # Per-author
        w.writerow(["section", "author", "precision", "recall", "f1", "support"])
        for am in result.per_author:
            w.writerow([
                "author", am.author,
                f"{am.precision:.6f}", f"{am.recall:.6f}",
                f"{am.f1:.6f}", am.support,
            ])
        w.writerow([])

        # Confusion matrix
        authors = sorted(result.confusion_matrix.keys())
        w.writerow(["section", "true\\predicted"] + authors)
        for true_author in authors:
            row = result.confusion_matrix[true_author]
            w.writerow(["confusion", true_author] + [row.get(a, 0) for a in authors])
        w.writerow([])

        # Per-prediction detail
        w.writerow(["section", "fold", "document", "true_author", "predicted_author"])
        for fr in result.fold_results:
            for p in fr.predictions:
                w.writerow(["prediction", fr.fold_index, p.document_title,
                            p.true_author, p.predicted_author])
    finally:
        if should_close:
            output.close()

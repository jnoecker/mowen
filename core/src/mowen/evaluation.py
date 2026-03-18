"""Cross-validation and evaluation metrics for authorship attribution."""

from __future__ import annotations

import csv
import logging
import random
from dataclasses import dataclass
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
    eer: float | None = None
    c_at_1: float | None = None
    f05u: float | None = None
    brier: float | None = None


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------


def _compute_eer(predictions: list[Prediction]) -> float | None:
    """Compute Equal Error Rate for verification-style scores.

    For each author (one-vs-rest), uses the ranking scores as a confidence
    signal.  EER is the threshold where false-accept rate equals false-reject
    rate.  Returns the macro-averaged EER across authors, or None if scores
    are unavailable.
    """
    if not predictions or not predictions[0].scores:
        return None

    all_authors = sorted({p.true_author for p in predictions})
    if len(all_authors) < 2:
        return None

    eer_sum = 0.0
    counted = 0

    for target in all_authors:
        # Build (score, is_positive) pairs
        pairs: list[tuple[float, bool]] = []
        for p in predictions:
            is_positive = p.true_author == target
            # Find score for this target author in the ranking
            score = None
            for author, s in p.scores:
                if author == target:
                    score = s
                    break
            if score is None:
                continue
            pairs.append((score, is_positive))

        positives = sum(1 for _, pos in pairs if pos)
        negatives = len(pairs) - positives
        if positives == 0 or negatives == 0:
            continue

        # Sort by score descending (higher = more confident for this author)
        pairs.sort(key=lambda x: x[0], reverse=True)

        # Walk thresholds to find where FAR crosses FRR
        best_eer = 1.0
        tp = 0
        fp = 0
        for score, is_pos in pairs:
            if is_pos:
                tp += 1
            else:
                fp += 1
            fnr = 1.0 - tp / positives  # false negative rate
            fpr = fp / negatives  # false positive rate
            # EER is approximately where FPR == FNR
            best_eer = min(best_eer, max(fpr, fnr) if abs(fpr - fnr) < 0.5 else best_eer)
            if fpr >= fnr:
                # Interpolate
                best_eer = min(best_eer, (fpr + fnr) / 2)
                break

        eer_sum += best_eer
        counted += 1

    return eer_sum / counted if counted > 0 else None


def _compute_c_at_1(predictions: list[Prediction]) -> float | None:
    """Compute c@1 metric (Pen~as & Rodrigo, 2011).

    c@1 = (1/n) * (nc + nu * nc/n)

    where nc = correct predictions, nu = unanswered (score below threshold
    or tied), n = total.  For closed-set attribution, nu = 0, so c@1 = accuracy.
    For verification methods with a threshold, predictions where the top score
    equals the verification threshold are treated as unanswered.
    """
    if not predictions:
        return None

    n = len(predictions)
    nc = sum(1 for p in predictions if p.true_author == p.predicted_author)
    # Count non-answers: top score is exactly 0.5 (verification abstention)
    nu = 0
    if predictions[0].scores:
        nu = sum(
            1 for p in predictions
            if p.scores and p.scores[0][1] == 0.5
        )
    return (nc + nu * nc / n) / n if n > 0 else None


def _compute_f05u(predictions: list[Prediction]) -> float | None:
    """Compute F_0.5u metric (Bevendorff et al., 2019).

    A precision-weighted F-measure for verification that rewards leaving
    hard cases unanswered (score = 0.5).  Non-answers are treated as
    neither correct nor incorrect but earn a bonus proportional to the
    overall accuracy.

    For closed-set attribution where all predictions are answered,
    this equals the standard F_0.5 on the binary correct/incorrect
    framing.
    """
    if not predictions:
        return None

    n = len(predictions)
    # Count non-answers: top score is exactly 0.5 (verification abstention)
    nu = 0
    if predictions[0].scores:
        nu = sum(1 for p in predictions if p.scores and p.scores[0][1] == 0.5)

    nc = sum(
        1 for p in predictions if p.true_author == p.predicted_author
    )
    # Answered predictions only
    n_answered = n - nu
    if n_answered == 0:
        # All unanswered — score based on c@1 logic
        return nc / n if n > 0 else None

    tp = nc
    fp = n_answered - nc
    fn = 0  # in the binary framing, fn = missed positives

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / n if n > 0 else 0.0

    beta_sq = 0.25  # beta = 0.5, beta^2 = 0.25
    if precision + recall == 0:
        f05 = 0.0
    else:
        f05 = (1 + beta_sq) * precision * recall / (beta_sq * precision + recall)

    # Credit for non-answers (same bonus structure as c@1)
    if n > 0 and nu > 0:
        answered_acc = nc / n_answered if n_answered > 0 else 0.0
        f05u = (n_answered * f05 + nu * answered_acc) / n
    else:
        f05u = f05

    return f05u


def _compute_brier(predictions: list[Prediction]) -> float | None:
    """Compute complement of Brier score for calibration quality.

    Brier complement = 1 - (1/n) * sum((confidence - label)^2)

    where confidence is the score assigned to the predicted (top-ranked)
    author, normalized to [0, 1], and label is 1 if the prediction is
    correct, 0 otherwise.  Higher is better; 1.0 is perfect.

    Returns None if ranking scores are unavailable.
    """
    if not predictions or not predictions[0].scores:
        return None

    n = len(predictions)
    brier_sum = 0.0

    for p in predictions:
        if not p.scores:
            return None
        # Top-ranked author's score as confidence
        confidence = p.scores[0][1]
        # Clamp to [0, 1] for methods that may produce scores outside range
        confidence = max(0.0, min(1.0, confidence))
        label = 1.0 if p.true_author == p.predicted_author else 0.0
        brier_sum += (confidence - label) ** 2

    return 1.0 - brier_sum / n


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

    eer = _compute_eer(all_preds)
    c1 = _compute_c_at_1(all_preds)
    f05u = _compute_f05u(all_preds)
    brier = _compute_brier(all_preds)

    return EvaluationResult(
        fold_results=fold_results,
        accuracy=accuracy,
        per_author=per_author,
        macro_precision=macro_p,
        macro_recall=macro_r,
        macro_f1=macro_f1,
        confusion_matrix=cm,
        eer=eer,
        c_at_1=c1,
        f05u=f05u,
        brier=brier,
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
# Cross-genre evaluation
# ---------------------------------------------------------------------------


def cross_genre_evaluate(
    documents: list[Document],
    config: PipelineConfig,
    train_genre: str,
    test_genre: str,
    *,
    progress_callback: ProgressCallback | None = None,
) -> EvaluationResult:
    """Evaluate across genres: train on one genre, test on another.

    Documents must have ``metadata["genre"]`` set.  Authors must appear
    in both genres.

    Parameters
    ----------
    documents:
        All documents with genre metadata.
    config:
        Pipeline configuration.
    train_genre:
        Genre to use for training.
    test_genre:
        Genre to use for testing.
    progress_callback:
        Optional ``(fraction, message)`` callback.

    Returns
    -------
    EvaluationResult
        Single-fold result from cross-genre evaluation.
    """
    train_docs = [
        d for d in documents if d.metadata.get("genre") == train_genre
    ]
    test_docs = [
        d for d in documents if d.metadata.get("genre") == test_genre
    ]

    if not train_docs:
        raise EvaluationError(
            f"No documents found with genre {train_genre!r}"
        )
    if not test_docs:
        raise EvaluationError(
            f"No documents found with genre {test_genre!r}"
        )

    # Validate all docs have authors
    for doc in train_docs + test_docs:
        if not doc.author:
            raise EvaluationError(
                f"Document {doc.title!r} has no author"
            )

    train_authors = {d.author for d in train_docs}
    test_authors = {d.author for d in test_docs}
    shared = train_authors & test_authors

    if len(shared) < 2:
        raise EvaluationError(
            f"Need >= 2 shared authors across genres, "
            f"found {len(shared)}: {shared}"
        )

    # Filter to shared authors only
    train_docs = [d for d in train_docs if d.author in shared]
    test_docs = [d for d in test_docs if d.author in shared]

    if progress_callback:
        progress_callback(0.0, "Cross-genre evaluation")

    results = Pipeline(config).execute(train_docs, test_docs)

    preds = [
        _make_prediction(r, test_docs[i].author or "")
        for i, r in enumerate(results)
    ]

    if progress_callback:
        progress_callback(1.0, "Evaluation complete")

    return _compute_metrics([FoldResult(fold_index=0, predictions=preds)])


# ---------------------------------------------------------------------------
# Topic-controlled evaluation
# ---------------------------------------------------------------------------


@dataclass
class TopicControlledResult:
    """Comparative results from topic-controlled evaluation."""

    within_topic: dict[str, EvaluationResult]  # topic -> result
    across_topic: EvaluationResult
    overall: EvaluationResult


def topic_controlled_evaluate(
    documents: list[Document],
    config: PipelineConfig,
    *,
    topic_key: str = "topic",
    progress_callback: ProgressCallback | None = None,
) -> TopicControlledResult:
    """Evaluate with topic controls to measure topic confounding.

    Produces three sets of results:

    * **within-topic**: LOO for each topic separately
    * **across-topic**: for each topic, train on other topics, test on it
    * **overall**: standard LOO ignoring topics

    Documents must have ``metadata[topic_key]`` set and an author.

    Parameters
    ----------
    documents:
        All documents with topic metadata.
    config:
        Pipeline configuration.
    topic_key:
        Metadata key for topic labels.
    progress_callback:
        Optional ``(fraction, message)`` callback.
    """
    # Validate
    for doc in documents:
        if topic_key not in doc.metadata:
            raise EvaluationError(
                f"Document {doc.title!r} missing metadata key "
                f"{topic_key!r}"
            )
        if not doc.author:
            raise EvaluationError(
                f"Document {doc.title!r} has no author"
            )

    # Group by topic
    by_topic: dict[str, list[Document]] = {}
    for doc in documents:
        topic = doc.metadata[topic_key]
        by_topic.setdefault(topic, []).append(doc)

    topics = sorted(by_topic.keys())

    # Within-topic: LOO per topic
    within: dict[str, EvaluationResult] = {}
    for i, topic in enumerate(topics):
        topic_docs = by_topic[topic]
        topic_authors = {d.author for d in topic_docs}
        if len(topic_authors) < 2 or len(topic_docs) < 2:
            logger.warning(
                "Topic %r skipped for within-topic: "
                "insufficient authors or documents",
                topic,
            )
            continue
        if progress_callback:
            frac = i / (len(topics) * 2)
            progress_callback(frac, f"Within-topic: {topic}")
        within[topic] = leave_one_out(topic_docs, config)

    # Across-topic: for each topic, train on others, test on it
    across_folds: list[FoldResult] = []
    for i, topic in enumerate(topics):
        test_docs = by_topic[topic]
        train_docs = [
            d for t, docs in by_topic.items()
            for d in docs if t != topic
        ]
        train_authors = {d.author for d in train_docs}
        if len(train_authors) < 2:
            logger.warning(
                "Topic %r skipped for across-topic: "
                "training set has < 2 authors",
                topic,
            )
            continue
        if progress_callback:
            frac = 0.5 + i / (len(topics) * 2)
            progress_callback(frac, f"Across-topic: {topic}")

        results = Pipeline(config).execute(train_docs, test_docs)
        preds = [
            _make_prediction(r, test_docs[j].author or "")
            for j, r in enumerate(results)
        ]
        across_folds.append(FoldResult(fold_index=i, predictions=preds))

    across = _compute_metrics(across_folds) if across_folds else EvaluationResult(
        fold_results=[], accuracy=0.0, per_author=[],
        macro_precision=0.0, macro_recall=0.0, macro_f1=0.0,
        confusion_matrix={},
    )

    # Overall: standard LOO
    if progress_callback:
        progress_callback(0.9, "Overall LOO")
    overall = leave_one_out(documents, config)

    if progress_callback:
        progress_callback(1.0, "Evaluation complete")

    return TopicControlledResult(
        within_topic=within,
        across_topic=across,
        overall=overall,
    )


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
        if result.eer is not None:
            w.writerow(["summary", "eer", f"{result.eer:.6f}"])
        if result.c_at_1 is not None:
            w.writerow(["summary", "c_at_1", f"{result.c_at_1:.6f}"])
        if result.f05u is not None:
            w.writerow(["summary", "f05u", f"{result.f05u:.6f}"])
        if result.brier is not None:
            w.writerow(["summary", "brier", f"{result.brier:.6f}"])
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

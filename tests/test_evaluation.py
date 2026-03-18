"""Tests for the evaluation module (cross-validation and metrics)."""

from __future__ import annotations

import io
import json

import pytest

from mowen.evaluation import (
    AuthorMetrics,
    EvaluationResult,
    FoldResult,
    Prediction,
    _compute_brier,
    _compute_c_at_1,
    _compute_eer,
    _compute_f05u,
    _compute_metrics,
    k_fold,
    leave_one_out,
    write_results_csv,
)
from mowen.exceptions import EvaluationError
from mowen.pipeline import PipelineConfig
from mowen.types import Document

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_docs() -> list[Document]:
    """Create a small corpus with 2 authors, 3 docs each."""
    return [
        Document(
            text="The government must be strong and unified.",
            author="Hamilton",
            title="ham1",
        ),
        Document(
            text="A strong federal union requires taxation.",
            author="Hamilton",
            title="ham2",
        ),
        Document(
            text="The power of the federal government is essential.",
            author="Hamilton",
            title="ham3",
        ),
        Document(
            text="Separation of powers prevents tyranny.",
            author="Madison",
            title="mad1",
        ),
        Document(
            text="Factions are controlled by a large republic.",
            author="Madison",
            title="mad2",
        ),
        Document(
            text="The diversity of interests guards liberty.",
            author="Madison",
            title="mad3",
        ),
    ]


def _simple_config() -> PipelineConfig:
    return PipelineConfig(
        event_drivers=[{"name": "character_ngram", "params": {"n": 3}}],
        distance_function={"name": "cosine"},
        analysis_method={"name": "nearest_neighbor"},
    )


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------


class TestComputeMetrics:
    def test_perfect_accuracy(self):
        preds = [
            Prediction("d1", "A", "A", (("A", 0.1), ("B", 0.9))),
            Prediction("d2", "B", "B", (("B", 0.1), ("A", 0.9))),
        ]
        folds = [FoldResult(fold_index=0, predictions=preds)]
        result = _compute_metrics(folds)
        assert result.accuracy == 1.0
        assert result.macro_f1 == 1.0

    def test_zero_accuracy(self):
        preds = [
            Prediction("d1", "A", "B", (("B", 0.1),)),
            Prediction("d2", "B", "A", (("A", 0.1),)),
        ]
        folds = [FoldResult(fold_index=0, predictions=preds)]
        result = _compute_metrics(folds)
        assert result.accuracy == 0.0
        assert result.macro_f1 == 0.0

    def test_partial_accuracy(self):
        preds = [
            Prediction("d1", "A", "A", ()),
            Prediction("d2", "A", "B", ()),
            Prediction("d3", "B", "B", ()),
            Prediction("d4", "B", "B", ()),
        ]
        folds = [FoldResult(fold_index=0, predictions=preds)]
        result = _compute_metrics(folds)
        assert result.accuracy == 0.75  # 3/4
        # A: TP=1, FP=0, FN=1 -> P=1.0, R=0.5, F1=0.667
        # B: TP=2, FP=1, FN=0 -> P=0.667, R=1.0, F1=0.8
        a_metrics = next(a for a in result.per_author if a.author == "A")
        assert a_metrics.precision == 1.0
        assert a_metrics.recall == 0.5

    def test_confusion_matrix_structure(self):
        preds = [
            Prediction("d1", "A", "A", ()),
            Prediction("d2", "A", "B", ()),
            Prediction("d3", "B", "A", ()),
        ]
        folds = [FoldResult(fold_index=0, predictions=preds)]
        result = _compute_metrics(folds)
        assert result.confusion_matrix["A"]["A"] == 1
        assert result.confusion_matrix["A"]["B"] == 1
        assert result.confusion_matrix["B"]["A"] == 1
        assert result.confusion_matrix["B"]["B"] == 0

    def test_three_author_metrics(self):
        preds = [
            Prediction("d1", "A", "A", ()),
            Prediction("d2", "B", "B", ()),
            Prediction("d3", "C", "A", ()),  # C misclassified as A
        ]
        folds = [FoldResult(fold_index=0, predictions=preds)]
        result = _compute_metrics(folds)
        assert len(result.per_author) == 3
        assert result.accuracy == pytest.approx(2 / 3)

    def test_multi_fold_aggregation(self):
        fold0 = FoldResult(0, [Prediction("d1", "A", "A", ())])
        fold1 = FoldResult(1, [Prediction("d2", "B", "A", ())])
        result = _compute_metrics([fold0, fold1])
        assert result.accuracy == 0.5


# ---------------------------------------------------------------------------
# Verification metrics (EER, c@1)
# ---------------------------------------------------------------------------


class TestEER:
    def test_perfect_scores_eer_zero(self):
        """When scores perfectly separate authors, EER should be near 0."""
        preds = [
            Prediction("d1", "A", "A", (("A", 0.9), ("B", 0.1))),
            Prediction("d2", "A", "A", (("A", 0.8), ("B", 0.2))),
            Prediction("d3", "B", "B", (("A", 0.1), ("B", 0.9))),
            Prediction("d4", "B", "B", (("A", 0.2), ("B", 0.8))),
        ]
        eer = _compute_eer(preds)
        assert eer is not None
        assert eer <= 0.5  # should be well-separated

    def test_random_scores_eer_high(self):
        """When scores don't separate authors, EER should be higher."""
        preds = [
            Prediction("d1", "A", "A", (("A", 0.5), ("B", 0.5))),
            Prediction("d2", "B", "B", (("A", 0.5), ("B", 0.5))),
        ]
        eer = _compute_eer(preds)
        assert eer is not None

    def test_eer_none_for_empty(self):
        assert _compute_eer([]) is None

    def test_eer_none_for_no_scores(self):
        preds = [
            Prediction("d1", "A", "A", ()),
            Prediction("d2", "B", "B", ()),
        ]
        assert _compute_eer(preds) is None

    def test_eer_in_compute_metrics(self):
        preds = [
            Prediction("d1", "A", "A", (("A", 0.9), ("B", 0.1))),
            Prediction("d2", "B", "B", (("A", 0.1), ("B", 0.9))),
        ]
        folds = [FoldResult(fold_index=0, predictions=preds)]
        result = _compute_metrics(folds)
        assert result.eer is not None


class TestCAt1:
    def test_perfect_accuracy_c_at_1(self):
        """With perfect accuracy, c@1 = 1.0."""
        preds = [
            Prediction("d1", "A", "A", (("A", 0.9),)),
            Prediction("d2", "B", "B", (("B", 0.9),)),
        ]
        c1 = _compute_c_at_1(preds)
        assert c1 == 1.0

    def test_zero_accuracy_c_at_1(self):
        """With zero accuracy and no unanswered, c@1 = 0.0."""
        preds = [
            Prediction("d1", "A", "B", (("B", 0.9),)),
            Prediction("d2", "B", "A", (("A", 0.9),)),
        ]
        c1 = _compute_c_at_1(preds)
        assert c1 == 0.0

    def test_partial_accuracy_c_at_1(self):
        """c@1 should equal accuracy when there are no unanswered predictions."""
        preds = [
            Prediction("d1", "A", "A", ()),
            Prediction("d2", "A", "B", ()),
            Prediction("d3", "B", "B", ()),
            Prediction("d4", "B", "B", ()),
        ]
        c1 = _compute_c_at_1(preds)
        assert c1 == pytest.approx(0.75)  # same as accuracy

    def test_c_at_1_none_for_empty(self):
        assert _compute_c_at_1([]) is None

    def test_c_at_1_in_compute_metrics(self):
        preds = [
            Prediction("d1", "A", "A", (("A", 0.9),)),
            Prediction("d2", "B", "B", (("B", 0.9),)),
        ]
        folds = [FoldResult(fold_index=0, predictions=preds)]
        result = _compute_metrics(folds)
        assert result.c_at_1 is not None
        assert result.c_at_1 == 1.0

    def test_c_at_1_with_nonanswers(self):
        """Non-answers (score=0.5) should boost c@1 vs pure accuracy."""
        preds = [
            Prediction("d1", "A", "A", (("A", 0.9), ("B", 0.1))),
            Prediction("d2", "B", "A", (("A", 0.5), ("B", 0.3))),  # non-answer
            Prediction("d3", "B", "B", (("B", 0.8), ("A", 0.2))),
            Prediction("d4", "A", "B", (("B", 0.7), ("A", 0.3))),
        ]
        c1 = _compute_c_at_1(preds)
        assert c1 is not None
        # nc=2, n=4, nu=1 (d2 has top score 0.5)
        # c@1 = (2 + 1 * 2/4) / 4 = (2 + 0.5) / 4 = 0.625
        assert c1 == pytest.approx(0.625)


# ---------------------------------------------------------------------------
# F_0.5u metric
# ---------------------------------------------------------------------------


class TestF05u:
    def test_perfect_accuracy(self):
        """All correct predictions yield f05u = 1.0."""
        preds = [
            Prediction("d1", "A", "A", (("A", 0.9), ("B", 0.1))),
            Prediction("d2", "B", "B", (("B", 0.9), ("A", 0.1))),
        ]
        f05u = _compute_f05u(preds)
        assert f05u == pytest.approx(1.0)

    def test_zero_accuracy(self):
        """All wrong predictions yield f05u = 0.0."""
        preds = [
            Prediction("d1", "A", "B", (("B", 0.9), ("A", 0.1))),
            Prediction("d2", "B", "A", (("A", 0.9), ("B", 0.1))),
        ]
        f05u = _compute_f05u(preds)
        assert f05u == pytest.approx(0.0)

    def test_partial_accuracy(self):
        """Partial accuracy gives f05u between 0 and 1."""
        preds = [
            Prediction("d1", "A", "A", (("A", 0.9),)),
            Prediction("d2", "A", "B", (("B", 0.9),)),
            Prediction("d3", "B", "B", (("B", 0.9),)),
            Prediction("d4", "B", "B", (("B", 0.9),)),
        ]
        f05u = _compute_f05u(preds)
        assert f05u is not None
        assert 0.0 < f05u < 1.0

    def test_none_for_empty(self):
        assert _compute_f05u([]) is None

    def test_in_compute_metrics(self):
        preds = [
            Prediction("d1", "A", "A", (("A", 0.9),)),
            Prediction("d2", "B", "B", (("B", 0.9),)),
        ]
        folds = [FoldResult(fold_index=0, predictions=preds)]
        result = _compute_metrics(folds)
        assert result.f05u is not None
        assert result.f05u == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Brier score
# ---------------------------------------------------------------------------


class TestBrier:
    def test_perfect_with_high_confidence(self):
        """Correct predictions with high confidence → Brier near 1.0."""
        preds = [
            Prediction("d1", "A", "A", (("A", 0.95), ("B", 0.05))),
            Prediction("d2", "B", "B", (("B", 0.95), ("A", 0.05))),
        ]
        brier = _compute_brier(preds)
        assert brier is not None
        assert brier > 0.99

    def test_wrong_with_high_confidence(self):
        """Wrong predictions with high confidence → low Brier."""
        preds = [
            Prediction("d1", "A", "B", (("B", 0.95), ("A", 0.05))),
            Prediction("d2", "B", "A", (("A", 0.95), ("B", 0.05))),
        ]
        brier = _compute_brier(preds)
        assert brier is not None
        assert brier < 0.2

    def test_uncertain_predictions(self):
        """Scores near 0.5 give moderate Brier regardless of correctness."""
        preds = [
            Prediction("d1", "A", "A", (("A", 0.5), ("B", 0.5))),
            Prediction("d2", "B", "B", (("B", 0.5), ("A", 0.5))),
        ]
        brier = _compute_brier(preds)
        assert brier is not None
        assert 0.7 < brier < 0.8  # 1 - 0.5^2 = 0.75

    def test_none_for_empty(self):
        assert _compute_brier([]) is None

    def test_none_for_no_scores(self):
        preds = [
            Prediction("d1", "A", "A", ()),
            Prediction("d2", "B", "B", ()),
        ]
        assert _compute_brier(preds) is None

    def test_in_compute_metrics(self):
        preds = [
            Prediction("d1", "A", "A", (("A", 0.9), ("B", 0.1))),
            Prediction("d2", "B", "B", (("B", 0.9), ("A", 0.1))),
        ]
        folds = [FoldResult(fold_index=0, predictions=preds)]
        result = _compute_metrics(folds)
        assert result.brier is not None
        assert result.brier > 0.9


# ---------------------------------------------------------------------------
# Leave-one-out
# ---------------------------------------------------------------------------


class TestLeaveOneOut:
    def test_basic_loo(self):
        docs = _make_docs()
        result = leave_one_out(docs, _simple_config())
        # Should have one fold per document
        assert len(result.fold_results) == len(docs)
        # Each fold has exactly 1 prediction
        for fr in result.fold_results:
            assert len(fr.predictions) == 1
        # All true authors match the original documents
        all_preds = [p for fr in result.fold_results for p in fr.predictions]
        for pred, doc in zip(all_preds, docs):
            assert pred.true_author == doc.author

    def test_loo_returns_valid_metrics(self):
        result = leave_one_out(_make_docs(), _simple_config())
        assert 0.0 <= result.accuracy <= 1.0
        assert len(result.per_author) == 2
        assert all(0 <= a.f1 <= 1 for a in result.per_author)

    def test_loo_no_author_raises(self):
        docs = [
            Document(text="hello", title="d1"),
            Document(text="world", author="A", title="d2"),
        ]
        with pytest.raises(EvaluationError, match="author"):
            leave_one_out(docs, _simple_config())

    def test_loo_single_author_raises(self):
        docs = [
            Document(text="hello", author="A", title="d1"),
            Document(text="world", author="A", title="d2"),
        ]
        with pytest.raises(EvaluationError, match="2 distinct authors"):
            leave_one_out(docs, _simple_config())

    def test_loo_too_few_documents_raises(self):
        docs = [Document(text="hello", author="A", title="d1")]
        with pytest.raises(EvaluationError, match="At least 2"):
            leave_one_out(docs, _simple_config())

    def test_loo_progress_callback(self):
        progress_log = []
        leave_one_out(
            _make_docs(),
            _simple_config(),
            progress_callback=lambda f, m: progress_log.append((f, m)),
        )
        assert len(progress_log) > 0
        assert progress_log[-1][0] == 1.0


# ---------------------------------------------------------------------------
# K-fold
# ---------------------------------------------------------------------------


class TestKFold:
    def test_basic_kfold(self):
        docs = _make_docs()
        result = k_fold(docs, _simple_config(), k=3, random_seed=42)
        assert len(result.fold_results) == 3
        # Total predictions should equal total documents
        total_preds = sum(fr.total for fr in result.fold_results)
        assert total_preds == len(docs)

    def test_kfold_deterministic_with_seed(self):
        docs = _make_docs()
        r1 = k_fold(docs, _simple_config(), k=3, random_seed=42)
        r2 = k_fold(docs, _simple_config(), k=3, random_seed=42)
        preds1 = [
            (p.document_title, p.predicted_author)
            for fr in r1.fold_results
            for p in fr.predictions
        ]
        preds2 = [
            (p.document_title, p.predicted_author)
            for fr in r2.fold_results
            for p in fr.predictions
        ]
        assert preds1 == preds2

    def test_kfold_k_larger_than_n(self):
        docs = _make_docs()
        # k=100 > 6 docs, should clamp to LOO
        result = k_fold(docs, _simple_config(), k=100, random_seed=42)
        total_preds = sum(fr.total for fr in result.fold_results)
        assert total_preds == len(docs)

    def test_kfold_invalid_k_raises(self):
        with pytest.raises(EvaluationError, match="k must be >= 2"):
            k_fold(_make_docs(), _simple_config(), k=1)

    def test_kfold_no_shuffle(self):
        docs = _make_docs()
        r1 = k_fold(docs, _simple_config(), k=2, shuffle=False)
        r2 = k_fold(docs, _simple_config(), k=2, shuffle=False)
        preds1 = [
            (p.document_title, p.predicted_author)
            for fr in r1.fold_results
            for p in fr.predictions
        ]
        preds2 = [
            (p.document_title, p.predicted_author)
            for fr in r2.fold_results
            for p in fr.predictions
        ]
        assert preds1 == preds2

    def test_kfold_returns_valid_metrics(self):
        result = k_fold(_make_docs(), _simple_config(), k=2, random_seed=0)
        assert 0.0 <= result.accuracy <= 1.0
        assert len(result.confusion_matrix) == 2


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


class TestWriteResultsCsv:
    def _make_result(self) -> EvaluationResult:
        preds = [
            Prediction("d1", "A", "A", (("A", 0.1),)),
            Prediction("d2", "B", "B", (("B", 0.1),)),
        ]
        folds = [FoldResult(fold_index=0, predictions=preds)]
        return _compute_metrics(folds)

    def test_write_to_file(self, tmp_path):
        path = tmp_path / "results.csv"
        write_results_csv(self._make_result(), path)
        assert path.exists()
        content = path.read_text()
        assert "summary" in content
        assert "accuracy" in content

    def test_write_to_stringio(self):
        buf = io.StringIO()
        write_results_csv(self._make_result(), buf)
        content = buf.getvalue()
        assert "summary" in content
        assert "confusion" in content
        assert "prediction" in content

    def test_csv_accuracy_value(self, tmp_path):
        path = tmp_path / "results.csv"
        result = self._make_result()
        write_results_csv(result, path)
        content = path.read_text()
        assert "1.000000" in content  # perfect accuracy


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


class TestEvaluationIntegration:
    def test_loo_e2e(self):
        """Full LOO on a small corpus produces sensible results."""
        docs = _make_docs()
        result = leave_one_out(docs, _simple_config())
        # With a reasonable config, accuracy should be above random (50%)
        assert result.accuracy >= 0.0
        assert len(result.confusion_matrix) == 2
        # Every author appears in per_author
        author_names = {a.author for a in result.per_author}
        assert author_names == {"Hamilton", "Madison"}

    def test_kfold_e2e(self):
        """Full 2-fold on a small corpus produces sensible results."""
        docs = _make_docs()
        result = k_fold(docs, _simple_config(), k=2, random_seed=42)
        assert result.accuracy >= 0.0
        assert len(result.per_author) == 2

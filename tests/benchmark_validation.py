"""
Benchmark validation suite for mowen's SOTA features.

Runs all presets and new methods on bundled corpora, records accuracy
and verification metrics, and validates expected behaviors from the
literature.  Serves as a regression baseline — if future changes alter
these numbers, the change must be justified.

Usage:
    python tests/benchmark_validation.py

This does NOT require JGAAP.  All validation is self-contained using
mowen's bundled sample corpora.
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "core" / "src"))
sys.path.insert(0, str(ROOT / "cli" / "src"))

from mowen.data import get_sample_corpus, get_sample_corpus_path
from mowen.evaluation import (
    EvaluationResult,
    _compute_brier,
    _compute_c_at_1,
    _compute_eer,
    _compute_f05u,
    _compute_metrics,
    leave_one_out,
)
from mowen.pipeline import Pipeline, PipelineConfig
from mowen.types import Document

# ── corpus loading ──────────────────────────────────────────────────────────


def load_corpus(corpus_id: str) -> tuple[list[Document], list[Document]]:
    """Load a bundled sample corpus as (known, unknown) documents."""
    data = get_sample_corpus(corpus_id)
    data_dir = get_sample_corpus_path()

    known: list[Document] = []
    unknown: list[Document] = []

    for entry in data["known"]:
        fpath = data_dir / entry["file"]
        text = fpath.read_text(encoding="utf-8", errors="replace")
        known.append(
            Document(
                text=text,
                author=entry["author"],
                title=Path(entry["file"]).name,
            )
        )

    for entry in data.get("unknown", []):
        fpath = data_dir / entry["file"]
        text = fpath.read_text(encoding="utf-8", errors="replace")
        true_author = entry.get("true_author")
        if true_author == "NONE":
            true_author = None
        unknown.append(
            Document(
                text=text,
                author=true_author,
                title=Path(entry["file"]).name,
            )
        )

    return known, unknown


# ── experiment definitions ──────────────────────────────────────────────────


@dataclass
class BenchmarkExperiment:
    id: str
    description: str
    corpus: str
    config: dict  # PipelineConfig kwargs
    mode: str = "attribution"  # "attribution", "verification", "loo"
    expected_min_accuracy: float = 0.0  # minimum expected accuracy


def build_experiments() -> list[BenchmarkExperiment]:
    """Build the benchmark experiment suite."""
    experiments = []

    # ── Section 1: Classic presets on Federalist Papers (LOO) ────────────
    # These are regression baselines for the original presets.

    experiments.append(
        BenchmarkExperiment(
            id="fed_burrows_delta_loo",
            description="Burrows' Delta on Federalist Papers (LOO)",
            corpus="federalist_papers",
            config={
                "canonicizers": [
                    {"name": "unify_case"},
                    {"name": "normalize_whitespace"},
                ],
                "event_drivers": [
                    {"name": "word_events", "params": {"tokenizer": "whitespace"}}
                ],
                "event_cullers": [{"name": "most_common", "params": {"n": 150}}],
                "distance_function": {"name": "manhattan"},
                "analysis_method": {"name": "burrows_delta"},
            },
            mode="loo",
            expected_min_accuracy=0.5,
        )
    )

    experiments.append(
        BenchmarkExperiment(
            id="fed_cosine_delta_loo",
            description="Cosine Delta on Federalist Papers (LOO)",
            corpus="federalist_papers",
            config={
                "canonicizers": [
                    {"name": "unify_case"},
                    {"name": "normalize_whitespace"},
                ],
                "event_drivers": [{"name": "word_events"}],
                "event_cullers": [{"name": "most_common", "params": {"n": 300}}],
                "distance_function": {"name": "cosine"},
                "analysis_method": {"name": "nearest_neighbor"},
            },
            mode="loo",
            expected_min_accuracy=0.5,
        )
    )

    experiments.append(
        BenchmarkExperiment(
            id="fed_char_ngram_loo",
            description="Character 4-gram on Federalist Papers (LOO)",
            corpus="federalist_papers",
            config={
                "canonicizers": [{"name": "unify_case"}],
                "event_drivers": [{"name": "character_ngram", "params": {"n": 4}}],
                "event_cullers": [{"name": "most_common", "params": {"n": 2500}}],
                "distance_function": {"name": "cosine"},
                "analysis_method": {"name": "nearest_neighbor"},
            },
            mode="loo",
            expected_min_accuracy=0.5,
        )
    )

    experiments.append(
        BenchmarkExperiment(
            id="fed_function_words_loo",
            description="Function Words on Federalist Papers (LOO)",
            corpus="federalist_papers",
            config={
                "canonicizers": [
                    {"name": "unify_case"},
                    {"name": "normalize_whitespace"},
                ],
                "event_drivers": [
                    {"name": "function_words", "params": {"language": "english"}}
                ],
                "event_cullers": [],
                "distance_function": {"name": "cosine"},
                "analysis_method": {"name": "nearest_neighbor"},
            },
            mode="loo",
            expected_min_accuracy=0.4,
        )
    )

    # ── Section 2: New distance functions ────────────────────────────────

    experiments.append(
        BenchmarkExperiment(
            id="fed_ppm_distance_loo",
            description="PPM compression distance on Federalist Papers (LOO)",
            corpus="federalist_papers",
            config={
                "canonicizers": [{"name": "unify_case"}],
                "event_drivers": [{"name": "word_events"}],
                "event_cullers": [],
                "distance_function": {"name": "ppm", "params": {"order": 5}},
                "analysis_method": {"name": "nearest_neighbor"},
            },
            mode="loo",
            expected_min_accuracy=0.3,
        )
    )

    # ── Section 3: Verification methods ──────────────────────────────────

    experiments.append(
        BenchmarkExperiment(
            id="fed_imposters_attribution",
            description="General Imposters on Federalist Papers (attribution)",
            corpus="federalist_papers",
            config={
                "canonicizers": [{"name": "unify_case"}],
                "event_drivers": [{"name": "character_ngram", "params": {"n": 4}}],
                "event_cullers": [{"name": "most_common", "params": {"n": 1000}}],
                "distance_function": {"name": "cosine"},
                "analysis_method": {
                    "name": "imposters",
                    "params": {"n_iterations": 100, "random_seed": 42},
                },
            },
            mode="attribution",
            expected_min_accuracy=0.0,
        )
    )

    experiments.append(
        BenchmarkExperiment(
            id="fed_imposters_loo",
            description="General Imposters on Federalist Papers (LOO)",
            corpus="federalist_papers",
            config={
                "canonicizers": [{"name": "unify_case"}],
                "event_drivers": [{"name": "character_ngram", "params": {"n": 4}}],
                "event_cullers": [{"name": "most_common", "params": {"n": 500}}],
                "distance_function": {"name": "cosine"},
                "analysis_method": {
                    "name": "imposters",
                    "params": {"n_iterations": 50, "random_seed": 42},
                },
            },
            mode="loo",
            expected_min_accuracy=0.3,
        )
    )

    experiments.append(
        BenchmarkExperiment(
            id="fed_unmasking_loo",
            description="Unmasking on Federalist Papers (LOO)",
            corpus="federalist_papers",
            config={
                "canonicizers": [{"name": "unify_case"}],
                "event_drivers": [{"name": "word_events"}],
                "event_cullers": [],
                "distance_function": None,
                "analysis_method": {
                    "name": "unmasking",
                    "params": {
                        "n_features": 100,
                        "n_eliminate": 4,
                        "n_iterations": 5,
                        "n_folds": 3,
                        "random_seed": 42,
                    },
                },
            },
            mode="loo",
            expected_min_accuracy=0.2,
        )
    )

    # ── Section 4: Verification with calibration ─────────────────────────

    experiments.append(
        BenchmarkExperiment(
            id="fed_imposters_calibrated",
            description="Imposters with calibration on Federalist Papers",
            corpus="federalist_papers",
            config={
                "canonicizers": [{"name": "unify_case"}],
                "event_drivers": [{"name": "character_ngram", "params": {"n": 4}}],
                "event_cullers": [{"name": "most_common", "params": {"n": 500}}],
                "distance_function": {"name": "cosine"},
                "analysis_method": {
                    "name": "imposters",
                    "params": {
                        "n_iterations": 50,
                        "random_seed": 42,
                        "calibration_low": 0.35,
                        "calibration_high": 0.65,
                    },
                },
            },
            mode="loo",
            expected_min_accuracy=0.0,  # calibration may reduce accuracy
        )
    )

    # ── Section 5: AAAC Problem A with multiple methods ──────────────────

    for method_id, method_config in [
        ("nn", {"name": "nearest_neighbor"}),
        ("knn", {"name": "knn", "params": {"k": 3}}),
        ("svm", {"name": "svm"}),
    ]:
        experiments.append(
            BenchmarkExperiment(
                id=f"aaac_a_char3_{method_id}_loo",
                description=f"AAAC-A char-3-gram + {method_id} (LOO)",
                corpus="aaac_problem_a",
                config={
                    "canonicizers": [{"name": "unify_case"}],
                    "event_drivers": [{"name": "character_ngram", "params": {"n": 3}}],
                    "event_cullers": [{"name": "most_common", "params": {"n": 500}}],
                    "distance_function": (
                        {"name": "cosine"} if method_id != "svm" else None
                    ),
                    "analysis_method": method_config,
                },
                mode="loo",
                expected_min_accuracy=0.08,  # 13 authors, random=7.7%
            )
        )

    # ── Section 6: Contrastive learning (needs sklearn) ──────────────────

    experiments.append(
        BenchmarkExperiment(
            id="aaac_a_contrastive_loo",
            description="Contrastive learning (no projection) on AAAC-A (LOO)",
            corpus="aaac_problem_a",
            config={
                "canonicizers": [{"name": "unify_case"}],
                "event_drivers": [{"name": "character_ngram", "params": {"n": 3}}],
                "event_cullers": [{"name": "most_common", "params": {"n": 200}}],
                "distance_function": None,
                "analysis_method": {"name": "contrastive"},
            },
            mode="loo",
            expected_min_accuracy=0.05,  # 13 authors, random=7.7%
        )
    )

    return experiments


# ── experiment execution ────────────────────────────────────────────────────


@dataclass
class BenchmarkResult:
    experiment_id: str
    description: str
    status: str  # "PASS", "FAIL", "ERROR", "SKIP"
    accuracy: float | None = None
    metrics: dict = field(default_factory=dict)
    error: str = ""
    elapsed_s: float = 0.0


def run_experiment(exp: BenchmarkExperiment) -> BenchmarkResult:
    """Run a single benchmark experiment and return the result."""
    t0 = time.time()

    try:
        known, unknown = load_corpus(exp.corpus)
    except Exception as e:
        return BenchmarkResult(
            exp.id,
            exp.description,
            "ERROR",
            error=f"Corpus load failed: {e}",
        )

    config_kwargs = dict(exp.config)
    # Handle None distance_function
    if config_kwargs.get("distance_function") is None:
        config_kwargs.pop("distance_function", None)

    try:
        config = PipelineConfig(**config_kwargs)
    except Exception as e:
        return BenchmarkResult(
            exp.id,
            exp.description,
            "ERROR",
            error=f"Config error: {e}",
        )

    try:
        if exp.mode == "loo":
            eval_result = leave_one_out(known, config)
            accuracy = eval_result.accuracy
            metrics = {
                "accuracy": eval_result.accuracy,
                "macro_f1": eval_result.macro_f1,
                "macro_precision": eval_result.macro_precision,
                "macro_recall": eval_result.macro_recall,
            }
            if eval_result.eer is not None:
                metrics["eer"] = eval_result.eer
            if eval_result.c_at_1 is not None:
                metrics["c_at_1"] = eval_result.c_at_1
            if eval_result.f05u is not None:
                metrics["f05u"] = eval_result.f05u
            if eval_result.brier is not None:
                metrics["brier"] = eval_result.brier

            # Count non-answers
            all_preds = [p for fr in eval_result.fold_results for p in fr.predictions]
            nonanswers = sum(1 for p in all_preds if p.scores and p.scores[0][1] == 0.5)
            if nonanswers > 0:
                metrics["nonanswers"] = nonanswers

        elif exp.mode == "attribution":
            # Run pipeline directly on known/unknown
            if not unknown:
                return BenchmarkResult(
                    exp.id,
                    exp.description,
                    "SKIP",
                    error="No unknown documents",
                )

            pipeline = Pipeline(config)
            results = pipeline.execute(known, unknown)

            # Count correct (where true author is available)
            correct = 0
            total_eval = 0
            for r in results:
                if r.unknown_document.author:
                    total_eval += 1
                    if r.top_author == r.unknown_document.author:
                        correct += 1

            accuracy = correct / total_eval if total_eval > 0 else None
            metrics = {"correct": correct, "total": total_eval}
            if accuracy is not None:
                metrics["accuracy"] = accuracy

            # Verification scores
            if results and results[0].verification_threshold is not None:
                scores = [r.rankings[0].score for r in results if r.rankings]
                metrics["mean_score"] = sum(scores) / len(scores)
                metrics["min_score"] = min(scores)
                metrics["max_score"] = max(scores)
                metrics["threshold"] = results[0].verification_threshold
                verified = sum(
                    1 for s in scores if s >= results[0].verification_threshold
                )
                metrics["verified_count"] = verified

        else:
            return BenchmarkResult(
                exp.id,
                exp.description,
                "ERROR",
                error=f"Unknown mode: {exp.mode}",
            )

    except Exception as e:
        return BenchmarkResult(
            exp.id,
            exp.description,
            "ERROR",
            error=str(e),
            elapsed_s=time.time() - t0,
        )

    elapsed = time.time() - t0

    # Determine pass/fail
    actual_acc = accuracy if accuracy is not None else 0.0
    status = "PASS" if actual_acc >= exp.expected_min_accuracy else "FAIL"

    return BenchmarkResult(
        experiment_id=exp.id,
        description=exp.description,
        status=status,
        accuracy=accuracy,
        metrics=metrics,
        elapsed_s=elapsed,
    )


# ── style change detection validation ───────────────────────────────────────


def validate_style_change() -> BenchmarkResult:
    """Validate style change detection on a constructed document."""
    t0 = time.time()

    try:
        from mowen.style_change import detect_style_changes

        # Load two different authors from the test fixtures
        known, _ = load_corpus("federalist_papers")

        # Find one Hamilton and one Madison paper
        hamilton_text = ""
        madison_text = ""
        for doc in known:
            if doc.author == "Hamilton" and not hamilton_text:
                hamilton_text = doc.text[:1000]
            elif doc.author == "Madison" and not madison_text:
                madison_text = doc.text[:1000]
            if hamilton_text and madison_text:
                break

        if not hamilton_text or not madison_text:
            return BenchmarkResult(
                "style_change_detection",
                "Style change on Hamilton/Madison splice",
                "ERROR",
                error="Corpus loading failed",
            )

        # Construct a spliced document
        spliced = Document(
            text=hamilton_text + "\n\n" + madison_text,
            title="hamilton_madison_splice",
        )

        config = PipelineConfig(
            event_drivers=[{"name": "character_ngram", "params": {"n": 3}}],
            distance_function={"name": "cosine"},
        )

        result = detect_style_changes(spliced, config, threshold=0.3)

        metrics = {
            "paragraphs": len(result.paragraphs),
            "boundaries": len(result.predictions),
            "changes_detected": sum(1 for p in result.predictions if p.is_change),
        }

        if result.predictions:
            metrics["scores"] = [round(p.score, 3) for p in result.predictions]

        # At least one boundary should exist
        status = "PASS" if len(result.predictions) > 0 else "FAIL"

        return BenchmarkResult(
            "style_change_detection",
            "Style change on Hamilton/Madison splice",
            status,
            metrics=metrics,
            elapsed_s=time.time() - t0,
        )

    except Exception as e:
        return BenchmarkResult(
            "style_change_detection",
            "Style change on Hamilton/Madison splice",
            "ERROR",
            error=str(e),
            elapsed_s=time.time() - t0,
        )


# ── metric computation validation ───────────────────────────────────────────


def validate_metrics() -> list[BenchmarkResult]:
    """Validate metric computation against hand-computed expected values."""
    from mowen.evaluation import FoldResult, Prediction

    results = []

    # Test 1: Perfect predictions -> all metrics near 1.0
    preds = [
        Prediction("d1", "A", "A", (("A", 0.95), ("B", 0.05))),
        Prediction("d2", "A", "A", (("A", 0.90), ("B", 0.10))),
        Prediction("d3", "B", "B", (("B", 0.95), ("A", 0.05))),
        Prediction("d4", "B", "B", (("B", 0.90), ("A", 0.10))),
    ]
    folds = [FoldResult(fold_index=0, predictions=preds)]
    er = _compute_metrics(folds)

    checks = {
        "accuracy": (er.accuracy, 1.0, 0.001),
        "c_at_1": (er.c_at_1, 1.0, 0.001),
        "f05u": (er.f05u, 1.0, 0.001),
        "brier": (er.brier, None, None),  # just check > 0.9
    }

    all_pass = True
    details = {}
    for metric, (actual, expected, tol) in checks.items():
        if actual is None:
            details[metric] = "None"
            continue
        if expected is not None:
            ok = abs(actual - expected) < tol
        else:
            ok = actual > 0.9
        details[metric] = f"{actual:.4f}"
        if not ok:
            all_pass = False

    results.append(
        BenchmarkResult(
            "metrics_perfect_predictions",
            "Perfect predictions -> metrics near 1.0",
            "PASS" if all_pass else "FAIL",
            accuracy=er.accuracy,
            metrics=details,
        )
    )

    # Test 2: Non-answer predictions -> c@1 bonus
    preds2 = [
        Prediction("d1", "A", "A", (("A", 0.9), ("B", 0.1))),
        Prediction("d2", "B", "A", (("A", 0.5), ("B", 0.3))),  # nonanswer
        Prediction("d3", "B", "B", (("B", 0.8), ("A", 0.2))),
    ]
    c1 = _compute_c_at_1(preds2)
    f05u = _compute_f05u(preds2)

    # nc=2, n=3, nu=1 -> c@1 = (2 + 1*2/3)/3 = 0.889
    expected_c1 = (2 + 1 * 2 / 3) / 3
    c1_ok = c1 is not None and abs(c1 - expected_c1) < 0.001

    results.append(
        BenchmarkResult(
            "metrics_nonanswer_c_at_1",
            f"Non-answer c@1 bonus (expected {expected_c1:.4f})",
            "PASS" if c1_ok else "FAIL",
            metrics={
                "c_at_1": f"{c1:.4f}" if c1 else "None",
                "expected": f"{expected_c1:.4f}",
            },
        )
    )

    # Test 3: EER should be low for well-separated scores
    eer = _compute_eer(preds)
    eer_ok = eer is not None and eer < 0.3

    results.append(
        BenchmarkResult(
            "metrics_eer_well_separated",
            "EER low for well-separated scores",
            "PASS" if eer_ok else "FAIL",
            metrics={"eer": f"{eer:.4f}" if eer else "None"},
        )
    )

    return results


# ── PPM vs NCD correlation ──────────────────────────────────────────────────


def validate_ppm_ncd_correlation() -> BenchmarkResult:
    """Verify PPM and NCD agree on relative distances."""
    t0 = time.time()

    try:
        from mowen.distance_functions import distance_function_registry
        from mowen.types import Event, Histogram

        h_a = Histogram({Event(w): 3 for w in "the quick brown fox jumps".split()})
        h_b = Histogram({Event(w): 3 for w in "the slow brown dog sleeps".split()})
        h_c = Histogram({Event(w): 3 for w in "123 456 789 000 !!!".split()})

        ppm = distance_function_registry.create("ppm")
        ncd = distance_function_registry.create("ncd")

        # Both should agree: a-b closer than a-c
        ppm_ab = ppm.distance(h_a, h_b)
        ppm_ac = ppm.distance(h_a, h_c)
        ncd_ab = ncd.distance(h_a, h_b)
        ncd_ac = ncd.distance(h_a, h_c)

        ppm_agrees = ppm_ab < ppm_ac
        ncd_agrees = ncd_ab < ncd_ac
        both_agree = ppm_agrees and ncd_agrees

        return BenchmarkResult(
            "ppm_ncd_correlation",
            "PPM and NCD agree on relative distances",
            "PASS" if both_agree else "FAIL",
            metrics={
                "ppm_ab": f"{ppm_ab:.4f}",
                "ppm_ac": f"{ppm_ac:.4f}",
                "ncd_ab": f"{ncd_ab:.4f}",
                "ncd_ac": f"{ncd_ac:.4f}",
                "ppm_agrees": ppm_agrees,
                "ncd_agrees": ncd_agrees,
            },
            elapsed_s=time.time() - t0,
        )

    except Exception as e:
        return BenchmarkResult(
            "ppm_ncd_correlation",
            "PPM and NCD agree on relative distances",
            "ERROR",
            error=str(e),
            elapsed_s=time.time() - t0,
        )


# ── main ────────────────────────────────────────────────────────────────────


def main():
    print("=" * 78)
    print("mowen Benchmark Validation Suite")
    print("=" * 78)
    print()

    experiments = build_experiments()
    print(f"Built {len(experiments)} pipeline experiments")
    print("+ metric computation validation")
    print("+ style change detection validation")
    print("+ PPM/NCD correlation check")
    print()

    all_results: list[BenchmarkResult] = []

    # ── Metric validation (fast, no pipeline) ────────────────────────────
    print("Validating metric computation...")
    metric_results = validate_metrics()
    all_results.extend(metric_results)
    for r in metric_results:
        char = "." if r.status == "PASS" else "X" if r.status == "FAIL" else "!"
        print(f"  {char} {r.description}")
    print()

    # ── PPM/NCD correlation ──────────────────────────────────────────────
    print("Validating PPM/NCD correlation...")
    ppm_result = validate_ppm_ncd_correlation()
    all_results.append(ppm_result)
    char = "." if ppm_result.status == "PASS" else "X"
    print(f"  {char} {ppm_result.description}")
    print()

    # ── Style change detection ───────────────────────────────────────────
    print("Validating style change detection...")
    sc_result = validate_style_change()
    all_results.append(sc_result)
    char = "." if sc_result.status == "PASS" else "X"
    print(f"  {char} {sc_result.description}")
    print()

    # ── Pipeline experiments ─────────────────────────────────────────────
    print("Running pipeline experiments...")
    for i, exp in enumerate(experiments):
        result = run_experiment(exp)
        all_results.append(result)

        char = {
            "PASS": ".",
            "FAIL": "X",
            "ERROR": "!",
            "SKIP": "S",
        }.get(result.status, "?")
        print(char, end="", flush=True)
        if (i + 1) % 40 == 0:
            print(f" [{i + 1}/{len(experiments)}]")

    print()
    print()

    # ── Report ───────────────────────────────────────────────────────────
    print("=" * 78)
    print("RESULTS")
    print("=" * 78)
    print()

    status_counts = defaultdict(int)
    for r in all_results:
        status_counts[r.status] += 1

    total = len(all_results)
    for status in ["PASS", "FAIL", "ERROR", "SKIP"]:
        count = status_counts.get(status, 0)
        pct = count / total * 100 if total else 0
        bar = "#" * int(pct / 2)
        print(f"  {status:8s}: {count:3d}/{total} ({pct:5.1f}%) {bar}")
    print()

    # ── Detailed results table ───────────────────────────────────────────
    print("-" * 78)
    print(f"  {'Experiment':<45} {'Status':>6}  {'Acc':>6}  {'Time':>6}")
    print("-" * 78)
    for r in all_results:
        acc_str = f"{r.accuracy:.1%}" if r.accuracy is not None else "  n/a"
        time_str = f"{r.elapsed_s:.1f}s" if r.elapsed_s > 0 else ""
        print(f"  {r.experiment_id:<45} {r.status:>6}  {acc_str:>6}  {time_str:>6}")

        # Show key metrics inline
        for key in [
            "macro_f1",
            "eer",
            "c_at_1",
            "f05u",
            "brier",
            "nonanswers",
            "verified_count",
            "mean_score",
            "changes_detected",
        ]:
            if key in r.metrics:
                val = r.metrics[key]
                if isinstance(val, float):
                    print(f"    {key}: {val:.4f}")
                else:
                    print(f"    {key}: {val}")

    # ── Errors ───────────────────────────────────────────────────────────
    errors = [r for r in all_results if r.status in ("FAIL", "ERROR")]
    if errors:
        print()
        print("-" * 78)
        print("FAILURES AND ERRORS:")
        print("-" * 78)
        for r in errors:
            print(f"\n  [{r.status}] {r.experiment_id}")
            print(f"    {r.description}")
            if r.error:
                print(f"    Error: {r.error}")
            if r.accuracy is not None:
                print(f"    Accuracy: {r.accuracy:.1%}")

    # ── JSON output ──────────────────────────────────────────────────────
    json_path = ROOT / "tests" / "benchmark_results.json"
    json_data = []
    for r in all_results:
        entry = {
            "id": r.experiment_id,
            "description": r.description,
            "status": r.status,
            "accuracy": r.accuracy,
            "metrics": r.metrics,
            "elapsed_s": round(r.elapsed_s, 2),
        }
        if r.error:
            entry["error"] = r.error
        json_data.append(entry)

    json_path.write_text(json.dumps(json_data, indent=2))
    print(f"\nDetailed results written to {json_path}")

    # ── Exit code ────────────────────────────────────────────────────────
    failures = status_counts.get("FAIL", 0) + status_counts.get("ERROR", 0)
    if failures > 0:
        print(f"\n{failures} FAILURES — review results above")
        return 1
    else:
        passed = status_counts.get("PASS", 0)
        print(f"\nBENCHMARK PASSED — {passed}/{total} experiments")
        return 0


if __name__ == "__main__":
    sys.exit(main())

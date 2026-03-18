"""
Parallel validation: run the same experiments through both JGAAP and mowen,
comparing rankings and scores to ensure behavioral consistency.

Usage:
    python tests/validate_against_jgaap.py

Requires JGAAP to be compiled in JGAAP/bin/.
"""

import csv
import json
import subprocess
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
JGAAP_DIR = ROOT / "JGAAP"
JGAAP_CLASSPATH = f"{JGAAP_DIR / 'bin'};{JGAAP_DIR / 'lib' / 'external' / '*'}"
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "corpus"
SAMPLE_CORPORA_DIR = ROOT / "core" / "src" / "mowen" / "data" / "sample_corpora"

# ── component name mapping: (mowen_name -> JGAAP_display_name) ───────────────

EVENT_DRIVERS = {
    "word_events": "Words",
    "character_events": "Characters",
    "character_ngram": "Character NGrams",
    "word_ngram": "Word NGrams",
    "punctuation": "Punctuation",
    "word_length": "Word Lengths",
    "sentence_length": "Sentence Length",
    "suffix": "Suffices",
    "mw_function_words": "MW Function Words",
    "vowel_initial_words": "Vowel-initial Words",
    "rare_words": "Rare Words",
    "sorted_character_ngram": "Sorted Character NGram",
    "sorted_word_ngram": "Sorted Word NGram",
    "punctuation_ngram": "Punctuation NGrams",
    "first_word_in_sentence": "First Word In Sentence",
}

DISTANCE_FUNCTIONS = {
    "cosine": "Cosine Distance",
    "manhattan": "Manhattan Distance",
    "euclidean": "Histogram Distance",
    "chi_square": "Chi Square Distance",
    "canberra": "Canberra Distance",
    "angular_separation": "Angular Separation Distance",
    "bhattacharyya": "Bhattacharyya Distance",
    "bray_curtis": "Bray Curtis Distance",
    "chord": "Chord Distance",
    "hellinger": "Hellinger Distance",
    "histogram_intersection": "Histogram Intersection Distance",
    "intersection": "Intersection Distance",
    "nominal_ks": "KS Distance",
    "kendall_correlation": "Kendall Correlation Distance",
    "keselj_weighted": "Keselj-weighted Distance",
    "kl_divergence": "Kullback Leibler Distance",
    "matusita": "Matusita Distance",
    "pearson_correlation": "Pearson Correlation Distance",
    "cross_entropy": "RN Cross Entropy",
    "soergel": "Soergle Distance",
    "wave_hedges": "Wave Hedges Distance",
    "wed": "WED Divergence",
}

ANALYSIS_METHODS = {
    "nearest_neighbor": "Nearest Neighbor Driver",
    "centroid": "Centroid Driver",
    "absolute_centroid": "Absolute Centroid Driver",
    "burrows_delta": "Burrows Delta",
}

CANONICIZERS = {
    "unify_case": "Unify Case",
    "normalize_whitespace": "Normalize Whitespace",
    "strip_punctuation": "Strip Punctuation",
    "strip_numbers": "Strip Numbers",
    "normalize_ascii": "Normalize ASCII",
    "punctuation_separator": "Punctuation Separator",
    "smash_i": "Smash I",
}

EVENT_CULLERS = {
    "most_common": "Most Common Events",
    "least_common": "Least Common Events",
    "extreme": "X-treme Culler",
}


# ── experiment definitions ───────────────────────────────────────────────────


@dataclass
class Experiment:
    id: str
    event_driver: str
    event_driver_params: dict = field(default_factory=dict)
    distance_function: str = "cosine"
    analysis_method: str = "nearest_neighbor"
    canonicizers: list = field(default_factory=list)
    event_cullers: list = field(default_factory=list)
    culler_params: dict = field(default_factory=dict)
    corpus: str = "fixtures"  # "fixtures" or "aaac_a"


def build_experiments() -> list[Experiment]:
    """Build a comprehensive matrix of experiments."""
    experiments = []

    # ── Group 1: Event driver sweep with cosine + nearest neighbor ────────
    for ed in [
        "word_events",
        "character_events",
        "punctuation",
        "word_length",
        "sentence_length",
        "suffix",
        "mw_function_words",
        "vowel_initial_words",
        "rare_words",
        "first_word_in_sentence",
    ]:
        experiments.append(
            Experiment(
                id=f"ed_{ed}_cosine_nn",
                event_driver=ed,
            )
        )

    # ── Group 2: N-gram variants ─────────────────────────────────────────
    for n in [2, 3, 4]:
        experiments.append(
            Experiment(
                id=f"ed_charngram_n{n}_cosine_nn",
                event_driver="character_ngram",
                event_driver_params={"n": n},
            )
        )
    for n in [2, 3]:
        experiments.append(
            Experiment(
                id=f"ed_wordngram_n{n}_cosine_nn",
                event_driver="word_ngram",
                event_driver_params={"n": n},
            )
        )
    for n in [2, 3]:
        experiments.append(
            Experiment(
                id=f"ed_sorted_charngram_n{n}_cosine_nn",
                event_driver="sorted_character_ngram",
                event_driver_params={"n": n},
            )
        )
    experiments.append(
        Experiment(
            id="ed_sorted_wordngram_n2_cosine_nn",
            event_driver="sorted_word_ngram",
            event_driver_params={"n": 2},
        )
    )
    experiments.append(
        Experiment(
            id="ed_punctngram_n2_cosine_nn",
            event_driver="punctuation_ngram",
            event_driver_params={"n": 2},
        )
    )

    # ── Group 3: Distance function sweep with word events + nearest neighbor
    for df in [
        "cosine",
        "manhattan",
        "euclidean",
        "chi_square",
        "canberra",
        "angular_separation",
        "bhattacharyya",
        "bray_curtis",
        "chord",
        "hellinger",
        "histogram_intersection",
        "intersection",
        "nominal_ks",
        "kendall_correlation",
        "keselj_weighted",
        "kl_divergence",
        "matusita",
        "pearson_correlation",
        "cross_entropy",
        "soergel",
        "wave_hedges",
        "wed",
    ]:
        experiments.append(
            Experiment(
                id=f"ed_words_df_{df}_nn",
                event_driver="word_events",
                distance_function=df,
            )
        )

    # ── Group 4: Analysis method sweep with word events + cosine ─────────
    for am in ["nearest_neighbor", "centroid", "absolute_centroid", "burrows_delta"]:
        experiments.append(
            Experiment(
                id=f"ed_words_cosine_am_{am}",
                event_driver="word_events",
                analysis_method=am,
            )
        )

    # ── Group 5: Canonicizer combinations ────────────────────────────────
    for canon in [
        "unify_case",
        "strip_punctuation",
        "strip_numbers",
        "normalize_whitespace",
    ]:
        experiments.append(
            Experiment(
                id=f"canon_{canon}_words_cosine_nn",
                event_driver="word_events",
                canonicizers=[canon],
            )
        )
    experiments.append(
        Experiment(
            id="canon_multi_words_cosine_nn",
            event_driver="word_events",
            canonicizers=["unify_case", "strip_punctuation"],
        )
    )

    # ── Group 6: Combined sweeps (char ngram + various distances) ────────
    for df in ["manhattan", "chi_square", "hellinger", "cosine"]:
        experiments.append(
            Experiment(
                id=f"ed_charngram3_df_{df}_nn",
                event_driver="character_ngram",
                event_driver_params={"n": 3},
                distance_function=df,
            )
        )

    # ── Group 7: Analysis methods × distance functions ───────────────────
    for am in ["centroid", "absolute_centroid"]:
        for df in ["cosine", "manhattan", "euclidean"]:
            experiments.append(
                Experiment(
                    id=f"ed_words_{df}_{am}",
                    event_driver="word_events",
                    distance_function=df,
                    analysis_method=am,
                )
            )

    # ── Group 8: Full pipeline combos on AAAC problem A ──────────────────
    for ed, df, am in [
        ("word_events", "cosine", "nearest_neighbor"),
        ("character_ngram", "manhattan", "nearest_neighbor"),
        ("word_ngram", "cosine", "centroid"),
        ("character_events", "euclidean", "nearest_neighbor"),
        ("mw_function_words", "cosine", "nearest_neighbor"),
        ("word_events", "chi_square", "centroid"),
        ("word_events", "cosine", "burrows_delta"),
        ("punctuation", "cosine", "nearest_neighbor"),
        ("word_length", "manhattan", "nearest_neighbor"),
        ("character_ngram", "cosine", "absolute_centroid"),
    ]:
        ed_params = (
            {"n": 3}
            if ed == "character_ngram"
            else {"n": 2} if ed == "word_ngram" else {}
        )
        experiments.append(
            Experiment(
                id=f"aaac_{ed}_{df}_{am}",
                event_driver=ed,
                event_driver_params=ed_params,
                distance_function=df,
                analysis_method=am,
                corpus="aaac_a",
            )
        )

    return experiments


# ── corpus loading ───────────────────────────────────────────────────────────


def load_fixtures_corpus():
    """Load the Hamilton/Madison test fixtures."""
    from mowen.types import Document

    known, unknown = [], []
    for name, author in [
        ("hamilton1.txt", "Hamilton"),
        ("hamilton2.txt", "Hamilton"),
        ("madison1.txt", "Madison"),
        ("madison2.txt", "Madison"),
    ]:
        text = (FIXTURES_DIR / name).read_text(encoding="utf-8")
        known.append(Document(text=text, author=author, title=name))

    text = (FIXTURES_DIR / "unknown1.txt").read_text(encoding="utf-8")
    unknown.append(Document(text=text, title="unknown1.txt"))

    return known, unknown


def load_aaac_a_corpus():
    """Load AAAC Problem A from mowen's bundled sample corpora."""
    from mowen.types import Document

    manifest_path = SAMPLE_CORPORA_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Find problem A
    problem_a = None
    for problem in manifest:
        if problem["id"] == "aaac_problem_a":
            problem_a = problem
            break

    if problem_a is None:
        raise RuntimeError("AAAC Problem A not found in manifest")

    known, unknown = [], []
    for entry in problem_a["known"]:
        fpath = SAMPLE_CORPORA_DIR / entry["file"]
        text = fpath.read_text(encoding="utf-8", errors="replace")
        known.append(
            Document(
                text=text,
                author=entry["author"],
                title=Path(entry["file"]).name,
            )
        )

    for entry in problem_a.get("unknown", []):
        fpath = SAMPLE_CORPORA_DIR / entry["file"]
        text = fpath.read_text(encoding="utf-8", errors="replace")
        unknown.append(
            Document(
                text=text,
                title=Path(entry["file"]).name,
            )
        )

    return known, unknown


def write_jgaap_csv(known, unknown, csv_path: Path):
    """Write documents in JGAAP CSV format (author,filepath,title)."""
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for doc in known:
            # Write text to a temp file since JGAAP needs file paths
            writer.writerow([doc.author, doc.metadata["_filepath"], ""])
        for doc in unknown:
            writer.writerow(["", doc.metadata["_filepath"], ""])


def prepare_corpus_files(known, unknown, tmpdir: Path):
    """Write document texts to files and return updated docs with file paths."""
    corpus_dir = tmpdir / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)

    new_known, new_unknown = [], []

    from mowen.types import Document

    for doc in known:
        fpath = corpus_dir / f"{doc.author}_{doc.title}"
        fpath.write_text(doc.text, encoding="utf-8")
        new_doc = Document(
            text=doc.text,
            author=doc.author,
            title=doc.title,
            metadata={"_filepath": str(fpath).replace("\\", "/")},
        )
        new_known.append(new_doc)

    for doc in unknown:
        fpath = corpus_dir / doc.title
        fpath.write_text(doc.text, encoding="utf-8")
        new_doc = Document(
            text=doc.text,
            title=doc.title,
            metadata={"_filepath": str(fpath).replace("\\", "/")},
        )
        new_unknown.append(new_doc)

    return new_known, new_unknown


# ── mowen execution ─────────────────────────────────────────────────────────


@dataclass
class Result:
    document: str
    author: str
    score: float


def run_mowen(exp: Experiment, known, unknown) -> list[Result]:
    """Run a single experiment through mowen."""
    from mowen.pipeline import Pipeline, PipelineConfig

    ed_spec = {"name": exp.event_driver}
    if exp.event_driver_params:
        ed_spec["params"] = exp.event_driver_params

    canon_specs = [{"name": c} for c in exp.canonicizers]
    culler_specs = []
    for c in exp.event_cullers:
        spec = {"name": c}
        if c in exp.culler_params:
            spec["params"] = exp.culler_params[c]
        culler_specs.append(spec)

    config = PipelineConfig(
        canonicizers=canon_specs,
        event_drivers=[ed_spec],
        event_cullers=culler_specs,
        distance_function={"name": exp.distance_function},
        analysis_method={"name": exp.analysis_method},
    )

    pipeline = Pipeline(config)
    pipeline_results = pipeline.execute(known, unknown)

    results = []
    for pr in pipeline_results:
        for attr in pr.rankings:
            results.append(
                Result(
                    document=pr.unknown_document.title,
                    author=attr.author,
                    score=attr.score,
                )
            )

    return results


# ── JGAAP execution ─────────────────────────────────────────────────────────


def format_jgaap_ed(ed_name: str, params: dict) -> str:
    """Format event driver name with parameters for JGAAP."""
    jgaap_name = EVENT_DRIVERS[ed_name]
    if params:
        param_str = "|".join(f"{k}:{v}" for k, v in params.items())
        # Map mowen param names to JGAAP param names
        param_str = param_str.replace("n:", "N:")
        return f"{jgaap_name}|{param_str}"
    return jgaap_name


def run_jgaap_batch(
    experiments: list[Experiment],
    corpus_map: dict[str, tuple],
    tmpdir: Path,
) -> dict[str, list[Result]]:
    """Run a batch of experiments through JGAAP."""
    config_path = tmpdir / "jgaap_config.tsv"
    output_path = tmpdir / "jgaap_results.tsv"

    # Build config file
    with open(config_path, "w", encoding="utf-8") as f:
        for exp in experiments:
            known, unknown = corpus_map[exp.corpus]
            csv_path = tmpdir / f"jgaap_{exp.corpus}.csv"

            # Only write CSV once per corpus
            if not csv_path.exists():
                write_jgaap_csv(known, unknown, csv_path)

            jgaap_ed = format_jgaap_ed(exp.event_driver, exp.event_driver_params)
            jgaap_df = DISTANCE_FUNCTIONS.get(exp.distance_function, "")
            jgaap_am = ANALYSIS_METHODS.get(exp.analysis_method, "")
            jgaap_canons = (
                "|".join(CANONICIZERS[c] for c in exp.canonicizers)
                if exp.canonicizers
                else ""
            )

            csv_path_str = str(csv_path).replace("\\", "/")
            f.write(
                f"{exp.id}\t{csv_path_str}\t{jgaap_ed}\t{jgaap_df}\t{jgaap_am}\t{jgaap_canons}\n"
            )

    # Run JGAAP
    cmd = [
        "java",
        "-cp",
        JGAAP_CLASSPATH,
        "com.jgaap.backend.BatchRunner",
        str(config_path).replace("\\", "/"),
        str(output_path).replace("\\", "/"),
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
        cwd=str(JGAAP_DIR),
    )

    if proc.returncode != 0:
        print(f"JGAAP stderr:\n{proc.stderr}", file=sys.stderr)

    # Parse results
    results_by_exp: dict[str, list[Result]] = defaultdict(list)
    if output_path.exists():
        with open(output_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) < 4:
                    continue
                exp_id = parts[0]
                doc_title = parts[1]
                author_field = parts[2]
                score = float(parts[3])

                # JGAAP nearest neighbor returns "Author -filepath"
                # Extract just the author name
                if " -" in author_field:
                    author = author_field.split(" -")[0].strip()
                else:
                    author = author_field.strip()

                results_by_exp[exp_id].append(
                    Result(
                        document=doc_title,
                        author=author,
                        score=score,
                    )
                )

    return dict(results_by_exp)


# ── comparison ───────────────────────────────────────────────────────────────


def aggregate_nn_results(results: list[Result]) -> dict[str, list[Result]]:
    """Aggregate per-document results to per-author best scores.

    JGAAP's nearest neighbor returns one score per known document.
    mowen aggregates to best score per author. This function does the
    same aggregation on JGAAP results so they can be compared.
    """
    by_doc: dict[str, dict[str, float]] = defaultdict(dict)

    for r in results:
        doc = r.document
        author = r.author
        if author not in by_doc[doc] or r.score < by_doc[doc][author]:
            by_doc[doc][author] = r.score

    aggregated = []
    for doc, authors in by_doc.items():
        for author, score in sorted(authors.items(), key=lambda x: x[1]):
            aggregated.append(Result(document=doc, author=author, score=score))

    return aggregated


@dataclass
class ComparisonResult:
    experiment_id: str
    status: str  # "MATCH", "RANK_MISMATCH", "SCORE_MISMATCH", "MISSING", "ERROR"
    details: str = ""
    max_score_diff: float = 0.0


def compare_results(
    exp: Experiment,
    mowen_results: list[Result],
    jgaap_results: list[Result],
) -> ComparisonResult:
    """Compare mowen and JGAAP results for an experiment."""
    if not jgaap_results:
        return ComparisonResult(exp.id, "MISSING", "No JGAAP results")
    if not mowen_results:
        return ComparisonResult(exp.id, "MISSING", "No mowen results")

    # For nearest_neighbor, JGAAP returns per-document scores; aggregate
    if exp.analysis_method == "nearest_neighbor":
        jgaap_agg = aggregate_nn_results(jgaap_results)
    else:
        jgaap_agg = jgaap_results

    # Group by document
    mowen_by_doc: dict[str, list[Result]] = defaultdict(list)
    jgaap_by_doc: dict[str, list[Result]] = defaultdict(list)

    for r in mowen_results:
        mowen_by_doc[r.document].append(r)
    for r in jgaap_agg:
        jgaap_by_doc[r.document].append(r)

    max_diff = 0.0
    rank_mismatches = []
    score_mismatches = []

    for doc in mowen_by_doc:
        m_results = sorted(mowen_by_doc[doc], key=lambda r: r.score)
        j_results = sorted(jgaap_by_doc.get(doc, []), key=lambda r: r.score)

        if not j_results:
            return ComparisonResult(
                exp.id,
                "MISSING",
                f"No JGAAP results for document {doc}",
            )

        # Compare rankings
        m_ranking = [r.author for r in m_results]
        j_ranking = [r.author for r in j_results]

        if m_ranking != j_ranking:
            rank_mismatches.append(f"{doc}: mowen={m_ranking} vs jgaap={j_ranking}")

        # Compare scores
        m_scores = {r.author: r.score for r in m_results}
        j_scores = {r.author: r.score for r in j_results}

        for author in m_scores:
            if author in j_scores:
                diff = abs(m_scores[author] - j_scores[author])
                max_diff = max(max_diff, diff)
                if diff > 1e-6:
                    score_mismatches.append(
                        f"{doc}/{author}: mowen={m_scores[author]:.10f} "
                        f"jgaap={j_scores[author]:.10f} diff={diff:.2e}"
                    )

    if rank_mismatches:
        return ComparisonResult(
            exp.id,
            "RANK_MISMATCH",
            "; ".join(rank_mismatches),
            max_diff,
        )

    if score_mismatches and max_diff > 1e-6:
        return ComparisonResult(
            exp.id,
            "SCORE_MISMATCH",
            "; ".join(score_mismatches[:3]),  # truncate
            max_diff,
        )

    return ComparisonResult(exp.id, "MATCH", f"max_diff={max_diff:.2e}", max_diff)


# ── main ─────────────────────────────────────────────────────────────────────


def main():
    import time

    print("=" * 78)
    print("mowen vs JGAAP Parallel Validation")
    print("=" * 78)
    print()

    experiments = build_experiments()
    print(f"Designed {len(experiments)} experiments across:")
    print(f"  - {len(set(e.event_driver for e in experiments))} event drivers")
    print(
        f"  - {len(set(e.distance_function for e in experiments))} distance functions"
    )
    print(f"  - {len(set(e.analysis_method for e in experiments))} analysis methods")
    print()

    # Load corpora
    print("Loading corpora...")
    fixtures_known, fixtures_unknown = load_fixtures_corpus()
    aaac_known, aaac_unknown = load_aaac_a_corpus()

    with tempfile.TemporaryDirectory(prefix="mowen_validation_") as tmpdir:
        tmpdir = Path(tmpdir)

        # Prepare file-backed copies for JGAAP
        fix_known, fix_unknown = prepare_corpus_files(
            fixtures_known, fixtures_unknown, tmpdir / "fixtures"
        )
        aaac_known_f, aaac_unknown_f = prepare_corpus_files(
            aaac_known, aaac_unknown, tmpdir / "aaac"
        )

        corpus_map = {
            "fixtures": (fix_known, fix_unknown),
            "aaac_a": (aaac_known_f, aaac_unknown_f),
        }

        # Run JGAAP batch
        print("Running JGAAP batch...")
        t0 = time.time()
        jgaap_results = run_jgaap_batch(experiments, corpus_map, tmpdir)
        jgaap_time = time.time() - t0
        print(f"  JGAAP completed in {jgaap_time:.1f}s")
        print(f"  Got results for {len(jgaap_results)}/{len(experiments)} experiments")
        print()

        # Run mowen experiments and compare
        print("Running mowen experiments and comparing...")
        t0 = time.time()

        comparisons: list[ComparisonResult] = []
        mowen_corpus_cache = {
            "fixtures": (fixtures_known, fixtures_unknown),
            "aaac_a": (aaac_known, aaac_unknown),
        }

        for i, exp in enumerate(experiments):
            known, unknown = mowen_corpus_cache[exp.corpus]

            try:
                mowen_res = run_mowen(exp, known, unknown)
            except Exception as e:
                comparisons.append(
                    ComparisonResult(exp.id, "ERROR", f"mowen error: {e}")
                )
                continue

            jgaap_res = jgaap_results.get(exp.id, [])
            comparison = compare_results(exp, mowen_res, jgaap_res)
            comparisons.append(comparison)

            status_char = {
                "MATCH": ".",
                "SCORE_MISMATCH": "~",
                "RANK_MISMATCH": "X",
                "MISSING": "?",
                "ERROR": "!",
            }.get(comparison.status, "?")
            print(status_char, end="", flush=True)

            if (i + 1) % 50 == 0:
                print(f" [{i + 1}/{len(experiments)}]")

        mowen_time = time.time() - t0
        print()
        print(f"  mowen completed in {mowen_time:.1f}s")
        print()

    # ── Report ───────────────────────────────────────────────────────────
    print("=" * 78)
    print("RESULTS")
    print("=" * 78)
    print()

    status_counts = defaultdict(int)
    for c in comparisons:
        status_counts[c.status] += 1

    total = len(comparisons)
    for status in ["MATCH", "SCORE_MISMATCH", "RANK_MISMATCH", "MISSING", "ERROR"]:
        count = status_counts.get(status, 0)
        pct = count / total * 100 if total else 0
        bar = "#" * int(pct / 2)
        print(f"  {status:18s}: {count:3d}/{total} ({pct:5.1f}%) {bar}")

    print()

    # Detail non-matches
    non_matches = [c for c in comparisons if c.status != "MATCH"]
    if non_matches:
        print("-" * 78)
        print("NON-MATCHING EXPERIMENTS:")
        print("-" * 78)
        for c in non_matches:
            print(f"\n  [{c.status}] {c.experiment_id}")
            if c.max_score_diff > 0:
                print(f"    Max score difference: {c.max_score_diff:.2e}")
            if c.details:
                # Truncate long details
                detail_lines = c.details.split("; ")
                for line in detail_lines[:5]:
                    print(f"    {line}")
                if len(detail_lines) > 5:
                    print(f"    ... and {len(detail_lines) - 5} more")
    else:
        print("ALL EXPERIMENTS MATCH!")

    print()
    print("=" * 78)

    # Score tolerance analysis
    score_diffs = [c.max_score_diff for c in comparisons if c.status == "MATCH"]
    if score_diffs:
        print(f"\nScore precision analysis (matching experiments):")
        print(f"  Max difference:  {max(score_diffs):.2e}")
        print(f"  Mean difference: {sum(score_diffs) / len(score_diffs):.2e}")
        within_1e10 = sum(1 for d in score_diffs if d < 1e-10)
        within_1e6 = sum(1 for d in score_diffs if d < 1e-6)
        print(f"  Within 1e-10:    {within_1e10}/{len(score_diffs)}")
        print(f"  Within 1e-6:     {within_1e6}/{len(score_diffs)}")

    # Exit code
    failures = status_counts.get("RANK_MISMATCH", 0) + status_counts.get("ERROR", 0)
    if failures > 0:
        print(f"\n{failures} FAILURES - behavioral differences detected!")
        return 1
    else:
        matches = status_counts.get("MATCH", 0) + status_counts.get("SCORE_MISMATCH", 0)
        print(f"\nVALIDATION PASSED - {matches}/{total} experiments consistent")
        return 0


if __name__ == "__main__":
    sys.exit(main())

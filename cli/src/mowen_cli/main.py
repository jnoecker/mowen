"""mowen CLI — authorship attribution from the command line."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(
    name="mowen",
    help="Authorship attribution toolkit.",
    no_args_is_help=True,
)


def _parse_param(raw: str) -> tuple[str, str, dict[str, str]]:
    """Parse 'name:key=val,key=val' into (name, {params}).

    Also accepts plain 'name' with no params.
    """
    if ":" not in raw:
        return raw, raw, {}
    name, param_str = raw.split(":", 1)
    params: dict[str, str] = {}
    for pair in param_str.split(","):
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        params[k.strip()] = v.strip()
    return name, name, params


def _spec(raw: str) -> dict:
    """Turn a CLI component string into a dict for PipelineConfig."""
    name, _, params = _parse_param(raw)
    return {"name": name, "params": params} if params else {"name": name}


def _build_config(
    event_driver: list[str],
    distance: str,
    analysis: str,
    canonicizer: list[str] | None,
    culler: list[str] | None,
) -> PipelineConfig:
    """Build a PipelineConfig from CLI option values."""
    from mowen.pipeline import PipelineConfig

    return PipelineConfig(
        canonicizers=[_spec(c) for c in (canonicizer or [])],
        event_drivers=[_spec(e) for e in event_driver],
        event_cullers=[_spec(c) for c in (culler or [])],
        distance_function=_spec(distance),
        analysis_method=_spec(analysis),
    )


def _make_progress_cb(output_json: bool):
    """Create a terminal progress-bar callback, or None if not appropriate."""
    if not output_json and sys.stderr.isatty():
        def on_progress(frac: float, msg: str) -> None:
            bar_len = 30
            filled = int(bar_len * frac)
            bar = "█" * filled + "░" * (bar_len - filled)
            typer.echo(f"\r  {bar} {frac:5.0%}  {msg:<40}", err=True, nl=False)

        return on_progress
    return None


# ---------------------------------------------------------------------------
# mowen run
# ---------------------------------------------------------------------------

@app.command()
def run(
    documents: Annotated[
        Path,
        typer.Option("--documents", "-d", help="CSV manifest: filepath,author (empty author = unknown)."),
    ],
    event_driver: Annotated[
        list[str],
        typer.Option("--event-driver", "-e", help="Event driver (name or name:param=val,...). Repeatable."),
    ],
    distance: Annotated[
        str,
        typer.Option("--distance", help="Distance function name."),
    ] = "cosine",
    analysis: Annotated[
        str,
        typer.Option("--analysis", "-a", help="Analysis method (name or name:param=val,...)."),
    ] = "nearest_neighbor",
    canonicizer: Annotated[
        list[str] | None,
        typer.Option("--canonicizer", "-c", help="Canonicizer (name or name:param=val,...). Repeatable."),
    ] = None,
    culler: Annotated[
        list[str] | None,
        typer.Option("--culler", help="Event culler (name or name:param=val,...). Repeatable."),
    ] = None,
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Output results as JSON."),
    ] = False,
    base_dir: Annotated[
        Path | None,
        typer.Option("--base-dir", help="Base directory for resolving relative paths in CSV."),
    ] = None,
) -> None:
    """Run an authorship attribution experiment."""
    from mowen.compat.jgaap_csv import load_jgaap_csv
    from mowen.exceptions import MowenError
    from mowen.pipeline import Pipeline

    # Load documents
    try:
        known, unknown = load_jgaap_csv(documents, base_dir=base_dir)
    except Exception as e:
        typer.echo(f"Error loading documents: {e}", err=True)
        raise typer.Exit(1)

    if not known:
        typer.echo("Error: no known (authored) documents found in CSV.", err=True)
        raise typer.Exit(1)
    if not unknown:
        typer.echo("Error: no unknown documents found in CSV. Leave the author column empty for unknowns.", err=True)
        raise typer.Exit(1)

    # Build pipeline config
    config = _build_config(event_driver, distance, analysis, canonicizer, culler)

    progress_cb = _make_progress_cb(output_json)

    # Execute
    try:
        results = Pipeline(config, progress_callback=progress_cb).execute(known, unknown)
    except MowenError as e:
        typer.echo(f"\nError: {e}", err=True)
        raise typer.Exit(1)

    if progress_cb:
        typer.echo("", err=True)  # newline after progress bar

    # Output
    if output_json:
        out = []
        for r in results:
            entry: dict = {
                "document": r.unknown_document.title,
                "rankings": [{"author": a.author, "score": a.score} for a in r.rankings],
            }
            if r.verification_threshold is not None:
                entry["verification_threshold"] = r.verification_threshold
                if r.rankings:
                    top_score = r.rankings[0].score
                    if top_score == 0.5:
                        entry["verdict"] = "INCONCLUSIVE"
                    elif top_score >= r.verification_threshold:
                        entry["verdict"] = "VERIFIED"
                    else:
                        entry["verdict"] = "REJECTED"
            out.append(entry)
        typer.echo(json.dumps(out, indent=2))
    else:
        for r in results:
            typer.echo(f"\n  {r.unknown_document.title}")
            typer.echo(f"  {'─' * 40}")
            for i, a in enumerate(r.rankings):
                marker = " → " if i == 0 else "   "
                # Show VERIFIED/REJECTED badge for verification methods
                badge = ""
                if r.verification_threshold is not None and i == 0:
                    if a.score == 0.5:
                        badge = "  INCONCLUSIVE"
                    elif a.score >= r.verification_threshold:
                        badge = "  VERIFIED"
                    else:
                        badge = "  REJECTED"
                typer.echo(f"  {marker}{a.author:<25} {a.score:.4f}{badge}")


# ---------------------------------------------------------------------------
# mowen list-components
# ---------------------------------------------------------------------------

@app.command("list-components")
def list_components(
    category: Annotated[
        str | None,
        typer.Argument(help="Filter by category: canonicizers, event-drivers, event-cullers, distance-functions, analysis-methods."),
    ] = None,
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Output as JSON."),
    ] = False,
) -> None:
    """List available pipeline components and their parameters."""
    from mowen.analysis_methods import analysis_method_registry
    from mowen.canonicizers import canonicizer_registry
    from mowen.distance_functions import distance_function_registry
    from mowen.event_cullers import event_culler_registry
    from mowen.event_drivers import event_driver_registry

    registries = {
        "canonicizers": canonicizer_registry,
        "event-drivers": event_driver_registry,
        "event-cullers": event_culler_registry,
        "distance-functions": distance_function_registry,
        "analysis-methods": analysis_method_registry,
    }

    if category and category not in registries:
        typer.echo(f"Unknown category: {category!r}. Choose from: {', '.join(registries)}", err=True)
        raise typer.Exit(1)

    selected = {category: registries[category]} if category else registries

    if output_json:
        out: dict = {
            cat_name: registry.describe_components()
            for cat_name, registry in selected.items()
        }
        typer.echo(json.dumps(out, indent=2))
    else:
        for cat_name, registry in selected.items():
            typer.echo(f"\n  {cat_name}")
            typer.echo(f"  {'═' * 50}")
            for comp in registry.describe_components():
                typer.echo(f"    {comp['name']:<30} {comp['display_name']}")
                if comp["description"]:
                    typer.echo(f"      {comp['description']}")
                for p in comp.get("params", []):
                    constraint = ""
                    if p["choices"]:
                        constraint = f"  choices={p['choices']}"
                    elif p["min_value"] is not None or p["max_value"] is not None:
                        lo = p["min_value"] if p["min_value"] is not None else ""
                        hi = p["max_value"] if p["max_value"] is not None else ""
                        constraint = f"  range=[{lo}, {hi}]"
                    typer.echo(
                        f"        --{p['name']} ({p['type']}, default={p['default']}){constraint}"
                    )


# ---------------------------------------------------------------------------
# mowen convert-jgaap
# ---------------------------------------------------------------------------

@app.command("convert-jgaap")
def convert_jgaap(
    csv_file: Annotated[
        Path,
        typer.Argument(help="Path to JGAAP experiment CSV file."),
    ],
    base_dir: Annotated[
        Path | None,
        typer.Option("--base-dir", help="Base directory for resolving relative paths."),
    ] = None,
) -> None:
    """Convert a JGAAP CSV into a summary of loaded documents."""
    from mowen.compat.jgaap_csv import load_jgaap_csv

    try:
        known, unknown = load_jgaap_csv(csv_file, base_dir=base_dir)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"\n  Loaded {len(known)} known + {len(unknown)} unknown documents\n")

    if known:
        typer.echo("  Known documents:")
        authors: dict[str, int] = {}
        for doc in known:
            authors[doc.author or "?"] = authors.get(doc.author or "?", 0) + 1
        for author, count in sorted(authors.items()):
            typer.echo(f"    {author}: {count} document{'s' if count != 1 else ''}")

    if unknown:
        typer.echo("\n  Unknown documents:")
        for doc in unknown:
            preview = doc.text[:60].replace("\n", " ")
            typer.echo(f"    {doc.title}: {preview}...")


# ---------------------------------------------------------------------------
# mowen detect-changes
# ---------------------------------------------------------------------------

@app.command("detect-changes")
def detect_changes(
    document: Annotated[
        Path,
        typer.Argument(help="Path to a document file."),
    ],
    event_driver: Annotated[
        list[str],
        typer.Option(
            "--event-driver", "-e",
            help="Event driver. Repeatable.",
        ),
    ],
    distance: Annotated[
        str,
        typer.Option("--distance", help="Distance function."),
    ] = "cosine",
    threshold: Annotated[
        float,
        typer.Option("--threshold", "-t", help="Change detection threshold (0-1)."),
    ] = 0.5,
    separator: Annotated[
        str,
        typer.Option("--separator", help="Paragraph separator."),
    ] = "\n\n",
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Output as JSON."),
    ] = False,
) -> None:
    """Detect style changes (authorship boundaries) in a document."""
    from mowen.document_loaders import load_document
    from mowen.pipeline import PipelineConfig
    from mowen.style_change import detect_style_changes

    doc = load_document(str(document))
    config = PipelineConfig(
        event_drivers=[_spec(e) for e in event_driver],
        distance_function=_spec(distance),
    )

    result = detect_style_changes(
        doc, config, threshold=threshold, separator=separator,
    )

    if output_json:
        out = {
            "document": result.document.title,
            "paragraphs": len(result.paragraphs),
            "boundaries": [
                {
                    "index": p.boundary_index,
                    "score": round(p.score, 4),
                    "is_change": p.is_change,
                }
                for p in result.predictions
            ],
        }
        typer.echo(json.dumps(out, indent=2))
    else:
        typer.echo(f"\n  {result.document.title}")
        typer.echo(f"  {len(result.paragraphs)} paragraphs, "
                   f"{sum(1 for p in result.predictions if p.is_change)} "
                   f"change(s) detected\n")
        for i, para in enumerate(result.paragraphs):
            preview = para[:60].replace("\n", " ")
            typer.echo(f"  [{i + 1}] {preview}...")
            if i < len(result.predictions):
                p = result.predictions[i]
                marker = "CHANGE" if p.is_change else "  same"
                typer.echo(
                    f"       --- {marker} "
                    f"(score={p.score:.3f}) ---"
                )


# ---------------------------------------------------------------------------
# mowen evaluate
# ---------------------------------------------------------------------------

@app.command()
def evaluate(
    documents: Annotated[
        Path,
        typer.Option("--documents", "-d", help="CSV manifest: filepath,author. All rows must have authors."),
    ],
    event_driver: Annotated[
        list[str],
        typer.Option("--event-driver", "-e", help="Event driver (name or name:param=val,...). Repeatable."),
    ],
    distance: Annotated[
        str,
        typer.Option("--distance", help="Distance function name."),
    ] = "cosine",
    analysis: Annotated[
        str,
        typer.Option("--analysis", "-a", help="Analysis method (name or name:param=val,...)."),
    ] = "nearest_neighbor",
    canonicizer: Annotated[
        list[str] | None,
        typer.Option("--canonicizer", "-c", help="Canonicizer. Repeatable."),
    ] = None,
    culler: Annotated[
        list[str] | None,
        typer.Option("--culler", help="Event culler. Repeatable."),
    ] = None,
    mode: Annotated[
        str,
        typer.Option("--mode", "-m", help="Evaluation mode: loo or kfold."),
    ] = "loo",
    folds: Annotated[
        int,
        typer.Option("--folds", "-k", help="Number of folds for kfold mode."),
    ] = 10,
    seed: Annotated[
        int | None,
        typer.Option("--seed", help="Random seed for kfold shuffle."),
    ] = None,
    output_csv: Annotated[
        Path | None,
        typer.Option("--output-csv", "-o", help="Write results to CSV file."),
    ] = None,
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Output results as JSON."),
    ] = False,
    base_dir: Annotated[
        Path | None,
        typer.Option("--base-dir", help="Base directory for resolving relative paths in CSV."),
    ] = None,
    train_genre: Annotated[
        str | None,
        typer.Option("--train-genre", help="Genre to train on (cross-genre mode). CSV must have genre column."),
    ] = None,
    test_genre: Annotated[
        str | None,
        typer.Option("--test-genre", help="Genre to test on (cross-genre mode)."),
    ] = None,
    topic_controlled: Annotated[
        bool,
        typer.Option("--topic-controlled", help="Run topic-controlled evaluation (CSV needs topic column in metadata)."),
    ] = False,
    topic_key: Annotated[
        str,
        typer.Option("--topic-key", help="Metadata key for topic labels."),
    ] = "topic",
) -> None:
    """Evaluate pipeline accuracy via cross-validation."""
    from mowen.compat.jgaap_csv import load_jgaap_csv
    from mowen.evaluation import k_fold as kfold_eval
    from mowen.evaluation import leave_one_out as loo_eval
    from mowen.evaluation import write_results_csv
    from mowen.exceptions import EvaluationError, MowenError

    # Load documents
    try:
        known, unknown = load_jgaap_csv(documents, base_dir=base_dir)
    except Exception as e:
        typer.echo(f"Error loading documents: {e}", err=True)
        raise typer.Exit(1)

    if unknown:
        typer.echo(
            f"  Note: {len(unknown)} unknown document(s) ignored in evaluation mode.",
            err=True,
        )

    if not known:
        typer.echo("Error: no known (authored) documents found in CSV.", err=True)
        raise typer.Exit(1)

    config = _build_config(event_driver, distance, analysis, canonicizer, culler)

    progress_cb = _make_progress_cb(output_json)

    # Run evaluation
    try:
        if topic_controlled:
            from mowen.evaluation import topic_controlled_evaluate
            tc_result = topic_controlled_evaluate(
                known, config, topic_key=topic_key,
                progress_callback=progress_cb,
            )
            # Display topic-controlled results and exit early
            if progress_cb:
                typer.echo("", err=True)
            if output_json:
                out_tc: dict = {
                    "overall": {"accuracy": tc_result.overall.accuracy},
                    "across_topic": {"accuracy": tc_result.across_topic.accuracy},
                    "within_topic": {
                        t: {"accuracy": r.accuracy}
                        for t, r in tc_result.within_topic.items()
                    },
                }
                typer.echo(json.dumps(out_tc, indent=2))
            else:
                typer.echo("\n  Topic-Controlled Evaluation")
                typer.echo(f"  {'═' * 50}")
                typer.echo(f"\n  Overall accuracy: {tc_result.overall.accuracy:.1%}")
                typer.echo(f"  Across-topic accuracy: {tc_result.across_topic.accuracy:.1%}")
                typer.echo("\n  Within-topic:")
                for t, r in sorted(tc_result.within_topic.items()):
                    typer.echo(f"    {t:<25} {r.accuracy:.1%}")
            return
        elif train_genre and test_genre:
            from mowen.evaluation import cross_genre_evaluate
            result = cross_genre_evaluate(
                known, config, train_genre, test_genre,
                progress_callback=progress_cb,
            )
        elif mode == "loo":
            result = loo_eval(known, config, progress_callback=progress_cb)
        elif mode == "kfold":
            result = kfold_eval(
                known, config, k=folds, random_seed=seed,
                progress_callback=progress_cb,
            )
        else:
            typer.echo(f"Unknown mode: {mode!r}. Choose 'loo' or 'kfold'.", err=True)
            raise typer.Exit(1)
    except (EvaluationError, MowenError) as e:
        typer.echo(f"\nError: {e}", err=True)
        raise typer.Exit(1)

    if progress_cb:
        typer.echo("", err=True)

    # CSV export
    if output_csv:
        write_results_csv(result, output_csv)
        typer.echo(f"  Results written to {output_csv}", err=True)

    # Output
    if output_json:
        out: dict = {
            "accuracy": result.accuracy,
            "macro_precision": result.macro_precision,
            "macro_recall": result.macro_recall,
            "macro_f1": result.macro_f1,
            "per_author": [
                {"author": a.author, "precision": a.precision,
                 "recall": a.recall, "f1": a.f1, "support": a.support}
                for a in result.per_author
            ],
            "confusion_matrix": result.confusion_matrix,
            "predictions": [
                {"fold": fr.fold_index, "document": p.document_title,
                 "true_author": p.true_author, "predicted_author": p.predicted_author}
                for fr in result.fold_results for p in fr.predictions
            ],
        }
        if result.eer is not None:
            out["eer"] = result.eer
        if result.c_at_1 is not None:
            out["c_at_1"] = result.c_at_1
        if result.f05u is not None:
            out["f05u"] = result.f05u
        if result.brier is not None:
            out["brier"] = result.brier
        typer.echo(json.dumps(out, indent=2))
    else:
        n_docs = sum(fr.total for fr in result.fold_results)
        n_correct = sum(fr.correct for fr in result.fold_results)
        n_authors = len(result.per_author)
        mode_label = "leave-one-out" if mode == "loo" else f"{folds}-fold"

        typer.echo(f"\n  Cross-validation: {mode_label} ({n_docs} documents, {n_authors} authors)")
        typer.echo(f"  {'═' * 56}")
        typer.echo(f"\n  Accuracy: {result.accuracy:.1%} ({n_correct}/{n_docs})")

        typer.echo("\n  Per-author metrics:")
        typer.echo(f"    {'Author':<20} {'Precision':>9} {'Recall':>9} {'F1':>9} {'Support':>8}")
        typer.echo(f"    {'─' * 20} {'─' * 9} {'─' * 9} {'─' * 9} {'─' * 8}")
        for a in result.per_author:
            typer.echo(
                f"    {a.author:<20} {a.precision:>9.4f} {a.recall:>9.4f} "
                f"{a.f1:>9.4f} {a.support:>8}"
            )

        typer.echo(
            f"\n  Macro avg: P={result.macro_precision:.4f}  "
            f"R={result.macro_recall:.4f}  F1={result.macro_f1:.4f}"
        )

        # Verification-specific metrics
        has_verif = any(
            v is not None for v in
            (result.eer, result.c_at_1, result.f05u, result.brier)
        )
        if has_verif:
            parts = []
            if result.eer is not None:
                parts.append(f"EER={result.eer:.4f}")
            if result.c_at_1 is not None:
                parts.append(f"c@1={result.c_at_1:.4f}")
            if result.f05u is not None:
                parts.append(f"F0.5u={result.f05u:.4f}")
            if result.brier is not None:
                parts.append(f"Brier={result.brier:.4f}")
            typer.echo(f"  Verification: {'  '.join(parts)}")

        # Confusion matrix
        authors = sorted(result.confusion_matrix.keys())
        col_w = max(len(a) for a in authors) + 2
        col_w = max(col_w, 6)
        typer.echo("\n  Confusion matrix:")
        header = "    " + " " * col_w + "".join(f"{a:>{col_w}}" for a in authors)
        typer.echo(header)
        for true_a in authors:
            row = result.confusion_matrix[true_a]
            cells = "".join(f"{row.get(a, 0):>{col_w}}" for a in authors)
            typer.echo(f"    {true_a:<{col_w}}{cells}")

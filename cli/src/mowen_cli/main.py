"""mowen CLI — authorship attribution from the command line."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(
    name="mowen",
    help="Authorship attribution toolkit.",
    no_args_is_help=True,
)


def _parse_response(response: str) -> dict[str, str]:
    """Parse LLM response as JSON, or extract author name as fallback."""
    # Regular expression to match JSON structures with author key
    json_pattern = r'"author":\s*"([^"]+)"'
    match = re.search(json_pattern, response)
    if match:
        return {"author": match.group(1)}
    try:
        # Attempt to parse response as JSON
        return json.loads(response)
    except json.JSONDecodeError:
        # Fallback to searching for author name as plain text
        author_name = re.search(r'Author: ([^\n]+)', response).group(1)
        return {"author": author_name}


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
                typer.echo(f"    {comp['
"""mowen CLI — authorship attribution from the command line."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Optional

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
        Optional[list[str]],
        typer.Option("--canonicizer", "-c", help="Canonicizer (name or name:param=val,...). Repeatable."),
    ] = None,
    culler: Annotated[
        Optional[list[str]],
        typer.Option("--culler", help="Event culler (name or name:param=val,...). Repeatable."),
    ] = None,
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Output results as JSON."),
    ] = False,
    base_dir: Annotated[
        Optional[Path],
        typer.Option("--base-dir", help="Base directory for resolving relative paths in CSV."),
    ] = None,
) -> None:
    """Run an authorship attribution experiment."""
    from mowen.compat.jgaap_csv import load_jgaap_csv
    from mowen.exceptions import MowenError
    from mowen.pipeline import Pipeline, PipelineConfig

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
    def _spec(raw: str) -> dict:
        name, _, params = _parse_param(raw)
        return {"name": name, "params": params} if params else {"name": name}

    config = PipelineConfig(
        canonicizers=[_spec(c) for c in (canonicizer or [])],
        event_drivers=[_spec(e) for e in event_driver],
        event_cullers=[_spec(c) for c in (culler or [])],
        distance_function=_spec(distance),
        analysis_method=_spec(analysis),
    )

    # Progress callback for terminal
    if not output_json and sys.stderr.isatty():
        def on_progress(frac: float, msg: str) -> None:
            bar_len = 30
            filled = int(bar_len * frac)
            bar = "█" * filled + "░" * (bar_len - filled)
            typer.echo(f"\r  {bar} {frac:5.0%}  {msg:<40}", err=True, nl=False)

        progress_cb = on_progress
    else:
        progress_cb = None

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
        out = [
            {
                "document": r.unknown_document.title,
                "rankings": [{"author": a.author, "score": a.score} for a in r.rankings],
            }
            for r in results
        ]
        typer.echo(json.dumps(out, indent=2))
    else:
        for r in results:
            typer.echo(f"\n  {r.unknown_document.title}")
            typer.echo(f"  {'─' * 40}")
            for i, a in enumerate(r.rankings):
                marker = " → " if i == 0 else "   "
                typer.echo(f"  {marker}{a.author:<25} {a.score:.4f}")


# ---------------------------------------------------------------------------
# mowen list-components
# ---------------------------------------------------------------------------

@app.command("list-components")
def list_components(
    category: Annotated[
        Optional[str],
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
        out: dict = {}
        for cat_name, registry in selected.items():
            out[cat_name] = []
            for name, cls in registry.list_all().items():
                entry: dict = {
                    "name": name,
                    "display_name": getattr(cls, "display_name", name),
                    "description": getattr(cls, "description", ""),
                }
                if hasattr(cls, "param_defs"):
                    params = cls.param_defs()
                    if params:
                        entry["params"] = [
                            {
                                "name": p.name,
                                "type": p.param_type.__name__,
                                "default": p.default,
                                "description": p.description,
                            }
                            for p in params
                        ]
                out[cat_name].append(entry)
        typer.echo(json.dumps(out, indent=2))
    else:
        for cat_name, registry in selected.items():
            typer.echo(f"\n  {cat_name}")
            typer.echo(f"  {'═' * 50}")
            for name, cls in registry.list_all().items():
                display = getattr(cls, "display_name", name)
                desc = getattr(cls, "description", "")
                typer.echo(f"    {name:<30} {display}")
                if desc:
                    typer.echo(f"      {desc}")
                if hasattr(cls, "param_defs"):
                    for p in cls.param_defs():
                        constraint = ""
                        if p.choices:
                            constraint = f"  choices={p.choices}"
                        elif p.min_value is not None or p.max_value is not None:
                            lo = p.min_value if p.min_value is not None else ""
                            hi = p.max_value if p.max_value is not None else ""
                            constraint = f"  range=[{lo}, {hi}]"
                        typer.echo(
                            f"        --{p.name} ({p.param_type.__name__}, default={p.default}){constraint}"
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
        Optional[Path],
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
        typer.echo(f"\n  Unknown documents:")
        for doc in unknown:
            preview = doc.text[:60].replace("\n", " ")
            typer.echo(f"    {doc.title}: {preview}...")

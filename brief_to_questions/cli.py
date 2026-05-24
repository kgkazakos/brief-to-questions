"""Command-line interface for brief-to-questions.

LLM enrichment is on by default (use ``--no-llm`` for the offline rule-based
core). ``--json-output`` emits machine-readable JSON for pipelines and CI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from . import __version__
from .llm import available_backends
from .models import Severity
from .pipeline import analyse

_SEVERITY_STYLE = {
    Severity.CRITICAL: "bold red",
    Severity.WARNING: "yellow",
    Severity.INFO: "dim",
}


def _read_brief(path: str | None) -> str:
    if path and path != "-":
        return Path(path).read_text(encoding="utf-8")
    data = sys.stdin.read()
    if not data.strip():
        raise click.UsageError("No brief provided. Pass a file path or pipe text via stdin.")
    return data


def _emit_rich(analysis) -> None:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    console.print(Panel(analysis.summary, title="brief-to-questions", border_style="cyan"))

    if analysis.coverage_notes:
        notes = "\n".join(f"• {n}" for n in analysis.coverage_notes)
        console.print(Panel(notes, title="Coverage gaps", border_style="yellow"))

    table = Table(show_lines=True, expand=True, title="Research questions")
    table.add_column("P", justify="center", width=3)
    table.add_column("Question", ratio=3)
    table.add_column("Method", ratio=1)
    table.add_column("Informs", ratio=1)

    for q in analysis.questions:
        flag_str = ""
        if q.flags:
            flag_str = "\n" + "\n".join(
                f"[{_SEVERITY_STYLE[f.severity]}]⚑ {f.message}[/]" for f in q.flags
            )
        question_cell = f"{q.text}{flag_str}"
        table.add_row(str(q.priority), question_cell, q.method.value, q.informs_decision)

    console.print(table)
    backend = analysis.llm_backend or "rule-based (offline)"
    console.print(f"[dim]Engine: {backend} · {len(analysis.questions)} questions[/dim]")


@click.group()
@click.version_option(__version__, prog_name="brief-to-questions")
def cli() -> None:
    """Turn a product brief into research questions with recommended methods."""


@cli.command()
@click.argument("brief_path", required=False, type=click.Path(exists=False))
@click.option("--llm/--no-llm", "use_llm", default=True, help="Use LLM enrichment (default on).")
@click.option(
    "--backend",
    type=click.Choice(available_backends()),
    default="anthropic",
    show_default=True,
    help="LLM backend to use when enrichment is on.",
)
@click.option("--json-output", "json_output", is_flag=True, help="Emit JSON instead of a table.")
def analyze(brief_path: str | None, use_llm: bool, backend: str, json_output: bool) -> None:
    """Analyse a BRIEF_PATH file (or stdin) and print research questions."""
    brief = _read_brief(brief_path)
    warnings: list[str] = []
    analysis = analyse(brief, use_llm=use_llm, backend=backend, on_warning=warnings.append)

    if json_output:
        click.echo(json.dumps(analysis.to_dict(), indent=2))
        return

    for w in warnings:
        click.echo(click.style(f"warning: {w}", fg="yellow"), err=True)
    _emit_rich(analysis)


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--llm/--no-llm", "use_llm", default=True, help="Use LLM enrichment (default on).")
@click.option("--backend", type=click.Choice(available_backends()), default="anthropic", show_default=True)
@click.option("--pattern", default="*.md", show_default=True, help="Glob for brief files.")
def batch(directory: str, use_llm: bool, backend: str, pattern: str) -> None:
    """Analyse every brief in DIRECTORY and emit a JSON array."""
    results = []
    for path in sorted(Path(directory).glob(pattern)):
        analysis = analyse(path.read_text(encoding="utf-8"), use_llm=use_llm, backend=backend)
        results.append({"file": path.name, **analysis.to_dict()})
    click.echo(json.dumps(results, indent=2))


if __name__ == "__main__":
    cli()

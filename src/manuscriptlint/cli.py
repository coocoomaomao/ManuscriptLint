from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .checks import inspect_project, project_root
from .integrations import run_integration
from .models import Severity


app = typer.Typer(add_completion=False, no_args_is_help=True,
                  help="Preflight academic manuscripts before submission.")
console = Console()


@app.callback()
def main() -> None:
    """ManuscriptLint command group."""


@app.command()
def check(
    target: Path = typer.Argument(..., exists=True, readable=True,
                                  help="LaTeX file or project directory to inspect."),
    strict: bool = typer.Option(False, "--strict",
                                help="Exit with code 1 when warnings are present."),
    figurelint: bool = typer.Option(False, "--figurelint",
                                    help="Also run FigureLint on the project when installed."),
    reflint: bool = typer.Option(False, "--reflint",
                                 help="Also run RefLint on the project when installed."),
) -> None:
    """Check a LaTeX manuscript or project directory."""
    findings, tex_count, graphics, bib_files = inspect_project(target)
    root = project_root(target)

    if figurelint:
        findings.extend(run_integration("figurelint", root))
    if reflint:
        findings.extend(run_integration("reflint", root))

    table = Table(title="ManuscriptLint")
    table.add_column("File", overflow="fold")
    table.add_column("Line", justify="right")
    table.add_column("Severity")
    table.add_column("Code", no_wrap=True)
    table.add_column("Message", overflow="fold")

    if not findings:
        table.add_row(str(target), "—", "pass", "OK", "No findings.")

    errors = warnings = infos = 0
    for finding in findings:
        if finding.severity is Severity.ERROR:
            errors += 1
        elif finding.severity is Severity.WARNING:
            warnings += 1
        else:
            infos += 1
        table.add_row(
            str(finding.path),
            str(finding.line) if finding.line is not None else "—",
            finding.severity.value,
            finding.code,
            finding.message,
        )

    console.print(table)
    console.print(
        f"Checked {tex_count} LaTeX file(s), {len(graphics)} referenced figure(s), "
        f"{len(bib_files)} BibTeX library file(s): "
        f"{errors} error(s), {warnings} warning(s), {infos} info."
    )

    if errors:
        raise typer.Exit(code=2)
    if strict and warnings:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

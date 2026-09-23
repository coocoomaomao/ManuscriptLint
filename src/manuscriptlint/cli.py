from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .checks import inspect_project, project_root
from .github_annotations import emit_annotations
from .integrations import run_integration
from .models import Severity
from .reporting import json_report, summarize


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Preflight academic manuscripts before submission.",
)
console = Console()


@app.callback()
def main() -> None:
    """ManuscriptLint command group."""


@app.command()
def check(
    target: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="LaTeX file or project directory to inspect.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit with code 1 when warnings are present.",
    ),
    figurelint: bool = typer.Option(
        False,
        "--figurelint",
        help="Also run FigureLint on the project when installed.",
    ),
    reflint: bool = typer.Option(
        False,
        "--reflint",
        help="Also run RefLint on the project when installed.",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="Output format: text or json.",
    ),
    github_annotations: bool = typer.Option(
        False,
        "--github-annotations",
        help="Emit native GitHub Actions workflow annotations.",
    ),
) -> None:
    """Check a LaTeX manuscript or project directory."""
    output_format = output_format.lower()
    if output_format not in {"text", "json"}:
        raise typer.BadParameter("--format must be 'text' or 'json'.")
    if output_format == "json" and github_annotations:
        raise typer.BadParameter(
            "--format json cannot be combined with --github-annotations "
            "because annotations would make stdout invalid JSON."
        )

    findings, tex_count, graphics, bib_files = inspect_project(target)
    root = project_root(target)

    if figurelint:
        findings.extend(run_integration("figurelint", root))
    if reflint:
        findings.extend(run_integration("reflint", root))

    counts = summarize(findings)

    if output_format == "json":
        typer.echo(
            json.dumps(
                json_report(
                    target,
                    findings,
                    tex_count=tex_count,
                    graphics_count=len(graphics),
                    bib_count=len(bib_files),
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        if github_annotations:
            emit_annotations(findings)

        table = Table(title="ManuscriptLint")
        table.add_column("File", overflow="fold")
        table.add_column("Line", justify="right")
        table.add_column("Severity")
        table.add_column("Code", no_wrap=True)
        table.add_column("Message", overflow="fold")

        if not findings:
            table.add_row(str(target), "—", "pass", "OK", "No findings.")

        for finding in findings:
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
            f"{counts['errors']} error(s), {counts['warnings']} warning(s), "
            f"{counts['info']} info."
        )

    if counts["errors"]:
        raise typer.Exit(code=2)
    if strict and counts["warnings"]:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

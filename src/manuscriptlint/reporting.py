from __future__ import annotations

from pathlib import Path

from . import __version__
from .models import Finding, Severity


def summarize(findings: list[Finding]) -> dict[str, int]:
    return {
        "errors": sum(f.severity is Severity.ERROR for f in findings),
        "warnings": sum(f.severity is Severity.WARNING for f in findings),
        "info": sum(f.severity is Severity.INFO for f in findings),
    }


def json_report(
    target: Path,
    findings: list[Finding],
    *,
    tex_count: int,
    graphics_count: int,
    bib_count: int,
) -> dict[str, object]:
    counts = summarize(findings)
    return {
        "schema_version": 1,
        "tool": "ManuscriptLint",
        "tool_version": __version__,
        "target": str(target),
        "summary": {
            "tex_files": tex_count,
            "referenced_figures": graphics_count,
            "bib_libraries": bib_count,
            **counts,
        },
        "findings": [
            {
                "path": str(finding.path),
                "line": finding.line,
                "severity": finding.severity.value,
                "code": finding.code,
                "message": finding.message,
            }
            for finding in findings
        ],
    }

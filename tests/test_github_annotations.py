from pathlib import Path

from manuscriptlint.github_annotations import format_annotation
from manuscriptlint.models import Finding, Severity


def test_warning_annotation_includes_file_line_and_code() -> None:
    finding = Finding(
        path=Path("paper/main.tex"),
        severity=Severity.WARNING,
        code="TODO_LEFT",
        message="TODO remains.",
        line=12,
    )

    assert format_annotation(finding) == (
        "::warning file=paper/main.tex,title=TODO_LEFT,line=12::TODO remains."
    )


def test_annotation_escapes_workflow_command_characters() -> None:
    finding = Finding(
        path=Path("paper,a.tex"),
        severity=Severity.ERROR,
        code="REF:BAD",
        message="bad%ref\nnext",
        line=3,
    )

    rendered = format_annotation(finding)

    assert "file=paper%2Ca.tex" in rendered
    assert "title=REF%3ABAD" in rendered
    assert "bad%25ref%0Anext" in rendered

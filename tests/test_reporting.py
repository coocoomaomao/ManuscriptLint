import json
from pathlib import Path

from typer.testing import CliRunner

from manuscriptlint.cli import app


runner = CliRunner()


def test_json_output_is_machine_readable(tmp_path: Path) -> None:
    path = tmp_path / "paper.tex"
    path.write_text("TODO: revise discussion\n", encoding="utf-8")

    result = runner.invoke(app, ["check", str(path), "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == 1
    assert payload["tool"] == "ManuscriptLint"
    assert payload["summary"]["warnings"] == 1
    assert payload["findings"][0]["code"] == "TODO_LEFT"


def test_invalid_output_format_fails(tmp_path: Path) -> None:
    path = tmp_path / "paper.tex"
    path.write_text("\\section{Hello}\n", encoding="utf-8")

    result = runner.invoke(app, ["check", str(path), "--format", "xml"])

    assert result.exit_code != 0
    assert "text" in result.output
    assert "json" in result.output


def test_json_and_annotations_are_mutually_exclusive(tmp_path: Path) -> None:
    path = tmp_path / "paper.tex"
    path.write_text("\\section{Hello}\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["check", str(path), "--format", "json", "--github-annotations"],
    )

    assert result.exit_code != 0
    assert "invalid JSON" in result.output

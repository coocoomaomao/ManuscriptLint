from pathlib import Path

from typer.testing import CliRunner

from manuscriptlint.cli import app


runner = CliRunner()


def test_help_lists_check_command() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "check" in result.stdout


def test_check_clean_project(tmp_path: Path) -> None:
    path = tmp_path / "paper.tex"
    path.write_text("\\section{Hello}\n", encoding="utf-8")
    result = runner.invoke(app, ["check", str(path)])
    assert result.exit_code == 0
    assert "1 LaTeX file(s)" in result.stdout


def test_strict_fails_on_warning(tmp_path: Path) -> None:
    path = tmp_path / "paper.tex"
    path.write_text("TODO: fix me\n", encoding="utf-8")
    result = runner.invoke(app, ["check", str(path), "--strict"])
    assert result.exit_code == 1

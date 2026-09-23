from pathlib import Path

from manuscriptlint.latex import parse_tex, strip_comments


def test_strip_comments_preserves_escaped_percent() -> None:
    text = "value \\% stays % comment\nnext\n"
    cleaned = strip_comments(text)
    assert "value \\% stays " in cleaned
    assert "comment" not in cleaned
    assert cleaned.count("\n") == text.count("\n")


def test_parse_tex_extracts_core_commands(tmp_path: Path) -> None:
    path = tmp_path / "paper.tex"
    path.write_text(
        r"""\section{Intro}
\label{sec:intro}
See \ref{sec:intro} and \cite{cat2026,dog2025}.
\includegraphics[width=0.5\textwidth]{figures/result}
\bibliography{references}
""",
        encoding="utf-8",
    )
    parsed = parse_tex(path)
    assert parsed.labels[0][0] == "sec:intro"
    assert parsed.refs[0][0] == "sec:intro"
    assert [key for key, _ in parsed.cites] == ["cat2026", "dog2025"]
    assert parsed.graphics[0][0] == "figures/result"
    assert parsed.bibliographies[0][0] == "references"


def test_comments_do_not_create_findings(tmp_path: Path) -> None:
    path = tmp_path / "paper.tex"
    path.write_text("% TODO \\ref{ghost}\nText.\n", encoding="utf-8")
    parsed = parse_tex(path)
    assert parsed.refs == []
    assert parsed.todo_lines == []

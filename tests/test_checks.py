from pathlib import Path

from manuscriptlint.checks import inspect_project


def codes(findings) -> list[str]:
    return [finding.code for finding in findings]


def write_project(tmp_path: Path, tex: str, bib: str = "") -> Path:
    paper = tmp_path / "paper.tex"
    paper.write_text(tex, encoding="utf-8")
    if bib:
        (tmp_path / "references.bib").write_text(bib, encoding="utf-8")
    return paper


def test_clean_project_passes(tmp_path: Path) -> None:
    figures = tmp_path / "figures"
    figures.mkdir()
    (figures / "result.pdf").write_bytes(b"%PDF-placeholder")
    paper = write_project(
        tmp_path,
        r"""\section{Intro}\label{sec:intro}
See \ref{sec:intro} and \cite{cat2026}.
\begin{figure}
\includegraphics{figures/result}
\caption{A result.}
\label{fig:result}
\end{figure}
\bibliography{references}
""",
        """@article{cat2026,
  author = {Miao Cat},
  title = {A Study},
  journal = {Journal of Cats},
  year = {2026}
}
""",
    )
    findings, count, graphics, bibs = inspect_project(paper)
    assert findings == []
    assert count == 1
    assert len(graphics) == 1
    assert len(bibs) == 1


def test_duplicate_label_and_unresolved_ref_are_errors(tmp_path: Path) -> None:
    paper = write_project(tmp_path, r"""\label{dup}
\label{dup}
See \ref{missing}.
""")
    findings, *_ = inspect_project(paper)
    assert "LABEL_DUPLICATE" in codes(findings)
    assert "REF_UNRESOLVED" in codes(findings)


def test_missing_figure_and_source_are_errors(tmp_path: Path) -> None:
    paper = write_project(tmp_path, r"""\input{sections/missing}
\includegraphics{figures/missing}
""")
    findings, *_ = inspect_project(paper)
    assert "SOURCE_FILE_MISSING" in codes(findings)
    assert "FIGURE_FILE_MISSING" in codes(findings)


def test_missing_citation_key_is_error(tmp_path: Path) -> None:
    paper = write_project(
        tmp_path,
        r"""See \cite{missing2026}.
\bibliography{references}
""",
        """@article{cat2026,
  title = {A Study}
}
""",
    )
    findings, *_ = inspect_project(paper)
    assert "CITATION_MISSING" in codes(findings)


def test_caption_and_todo_warnings(tmp_path: Path) -> None:
    paper = write_project(tmp_path, r"""TODO: finish discussion.
\begin{figure}
Some content.
\end{figure}
\begin{table}
Some tabular content.
\end{table}
""")
    findings, *_ = inspect_project(paper)
    assert "TODO_LEFT" in codes(findings)
    assert "FIGURE_CAPTION_MISSING" in codes(findings)
    assert "TABLE_CAPTION_MISSING" in codes(findings)


def test_directory_scan_only_checks_reachable_tex_files(tmp_path: Path) -> None:
    (tmp_path / "main.tex").write_text(
        r"""\documentclass{article}
\begin{document}
\input{sections/intro}
\end{document}
""",
        encoding="utf-8",
    )
    sections = tmp_path / "sections"
    sections.mkdir()
    (sections / "intro.tex").write_text(
        r"""\section{Intro}\label{sec:intro}
See \ref{sec:intro}.
""",
        encoding="utf-8",
    )
    (tmp_path / "old-draft.tex").write_text(
        r"""Old draft points to \ref{ghost}.""",
        encoding="utf-8",
    )

    findings, count, *_ = inspect_project(tmp_path)

    assert count == 2
    assert "REF_UNRESOLVED" not in codes(findings)


def test_include_cycle_is_reported_without_looping(tmp_path: Path) -> None:
    (tmp_path / "main.tex").write_text(
        r"""\documentclass{article}
\input{part}
""",
        encoding="utf-8",
    )
    (tmp_path / "part.tex").write_text(r"""\input{main}""", encoding="utf-8")

    findings, count, *_ = inspect_project(tmp_path)

    assert count == 2
    assert "INCLUDE_CYCLE" in codes(findings)


def test_unused_figure_in_conventional_directory_is_info(tmp_path: Path) -> None:
    figures = tmp_path / "figures"
    figures.mkdir()
    (figures / "used.pdf").write_bytes(b"%PDF-used")
    (figures / "unused.png").write_bytes(b"png")
    (tmp_path / "main.tex").write_text(
        r"""\documentclass{article}
\usepackage{graphicx}
\includegraphics{figures/used}
""",
        encoding="utf-8",
    )

    findings, *_ = inspect_project(tmp_path)

    unused = [f for f in findings if f.code == "FIGURE_UNUSED"]
    assert len(unused) == 1
    assert unused[0].path.name == "unused.png"


def test_unused_bib_entry_is_info(tmp_path: Path) -> None:
    (tmp_path / "main.tex").write_text(
        r"""\documentclass{article}
See \cite{used}.
\bibliography{references}
""",
        encoding="utf-8",
    )
    (tmp_path / "references.bib").write_text(
        """@article{used,
  title = {Used}
}
@article{unused,
  title = {Unused}
}
""",
        encoding="utf-8",
    )

    findings, *_ = inspect_project(tmp_path)

    unused = [f for f in findings if f.code == "REFERENCE_UNUSED"]
    assert len(unused) == 1
    assert "unused" in unused[0].message


def test_nocite_star_suppresses_unused_reference_info(tmp_path: Path) -> None:
    (tmp_path / "main.tex").write_text(
        r"""\documentclass{article}
\nocite{*}
\bibliography{references}
""",
        encoding="utf-8",
    )
    (tmp_path / "references.bib").write_text(
        """@article{one,
  title = {One}
}
@article{two,
  title = {Two}
}
""",
        encoding="utf-8",
    )

    findings, *_ = inspect_project(tmp_path)

    assert "REFERENCE_UNUSED" not in codes(findings)

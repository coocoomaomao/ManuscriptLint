from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .latex import ParsedTex, discover_tex_files, parse_bib_keys, parse_tex
from .models import Finding, Severity


_IMAGE_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".svg", ".eps")


def project_root(target: Path) -> Path:
    return target if target.is_dir() else target.parent


def _resolve_source(source: ParsedTex, value: str) -> Path | None:
    raw = Path(value)
    candidates = [source.path.parent / raw]
    if raw.suffix == "":
        candidates.append(source.path.parent / raw.with_suffix(".tex"))
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _resolve_bibliography(source: ParsedTex, value: str, root: Path) -> Path | None:
    raw = Path(value)
    if raw.suffix == "":
        raw = raw.with_suffix(".bib")
    candidates = [source.path.parent / raw, root / raw]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _resolve_graphic(source: ParsedTex, value: str, root: Path) -> Path | None:
    raw = Path(value)
    bases = [source.path.parent, root]

    for graphicspath in source.graphicspaths:
        bases.extend([source.path.parent / graphicspath, root / graphicspath])

    seen: set[Path] = set()
    for base in bases:
        candidate = base / raw
        options = [candidate]
        if raw.suffix == "":
            options.extend(candidate.with_suffix(ext) for ext in _IMAGE_EXTENSIONS)
        for option in options:
            key = option.resolve()
            if key in seen:
                continue
            seen.add(key)
            if option.is_file():
                return option.resolve()
    return None


def inspect_project(target: Path) -> tuple[list[Finding], int, set[Path], set[Path]]:
    """Inspect manuscript structure and return findings plus discovered assets."""
    root = project_root(target).resolve()
    tex_files = discover_tex_files(target)
    findings: list[Finding] = []

    if not tex_files:
        return (
            [Finding(target, Severity.ERROR, "NO_TEX_FILES", "No LaTeX .tex files were found.")],
            0,
            set(),
            set(),
        )

    parsed: list[ParsedTex] = []
    for path in tex_files:
        try:
            parsed.append(parse_tex(path))
        except (OSError, UnicodeError) as exc:
            findings.append(
                Finding(path, Severity.ERROR, "TEX_UNREADABLE", f"Could not read LaTeX source: {exc}.")
            )

    labels: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    refs: list[tuple[str, Path, int]] = []
    cites: list[tuple[str, Path, int]] = []
    referenced_graphics: set[Path] = set()
    bib_files: set[Path] = set()

    for source in parsed:
        for label, line in source.labels:
            labels[label].append((source.path, line))
        refs.extend((ref, source.path, line) for ref, line in source.refs)
        cites.extend((cite, source.path, line) for cite, line in source.cites)

        for include, line in source.includes:
            if _resolve_source(source, include) is None:
                findings.append(
                    Finding(source.path, Severity.ERROR, "SOURCE_FILE_MISSING",
                            f"Included LaTeX source was not found: {include}.", line)
                )

        for graphic, line in source.graphics:
            resolved = _resolve_graphic(source, graphic, root)
            if resolved is None:
                findings.append(
                    Finding(source.path, Severity.ERROR, "FIGURE_FILE_MISSING",
                            f"Referenced figure file was not found: {graphic}.", line)
                )
            else:
                referenced_graphics.add(resolved)

        for bibliography, line in source.bibliographies:
            resolved = _resolve_bibliography(source, bibliography, root)
            if resolved is None:
                findings.append(
                    Finding(source.path, Severity.ERROR, "BIB_FILE_MISSING",
                            f"Referenced BibTeX file was not found: {bibliography}.", line)
                )
            else:
                bib_files.add(resolved)

        for line in source.figure_without_caption_lines:
            findings.append(Finding(source.path, Severity.WARNING, "FIGURE_CAPTION_MISSING",
                                    "Figure environment has no caption.", line))
        for line in source.table_without_caption_lines:
            findings.append(Finding(source.path, Severity.WARNING, "TABLE_CAPTION_MISSING",
                                    "Table environment has no caption.", line))
        for line in source.todo_lines:
            findings.append(Finding(source.path, Severity.WARNING, "TODO_LEFT",
                                    "TODO/FIXME marker remains in manuscript text.", line))

    for label, locations in sorted(labels.items()):
        if len(locations) >= 2:
            location_text = ", ".join(f"{p.name}:{line}" for p, line in locations)
            first_path, first_line = locations[0]
            findings.append(
                Finding(first_path, Severity.ERROR, "LABEL_DUPLICATE",
                        f"Label '{label}' is defined more than once ({location_text}).", first_line)
            )

    defined = set(labels)
    for ref, path, line in refs:
        if ref not in defined:
            findings.append(
                Finding(path, Severity.ERROR, "REF_UNRESOLVED",
                        f"Reference points to undefined label: {ref}.", line)
            )

    if cites:
        if not bib_files:
            findings.append(
                Finding(cites[0][1], Severity.INFO, "BIB_LIBRARY_UNKNOWN",
                        "Citations were found, but no existing BibTeX library was resolved "
                        "from \\bibliography or \\addbibresource.", cites[0][2])
            )
        else:
            bib_keys: set[str] = set()
            for bib_path in bib_files:
                bib_keys.update(parse_bib_keys(bib_path))
            for cite, path, line in cites:
                if cite != "*" and cite not in bib_keys:
                    findings.append(
                        Finding(path, Severity.ERROR, "CITATION_MISSING",
                                f"Citation key is missing from BibTeX libraries: {cite}.", line)
                    )

    return findings, len(parsed), referenced_graphics, bib_files

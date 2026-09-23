from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .latex import ParsedTex, discover_tex_files, parse_bib_entries, parse_tex
from .models import Finding, Severity


_IMAGE_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".svg", ".eps")
_FIGURE_DIR_NAMES = {"figures", "figure", "figs", "fig", "images", "image", "img"}


def project_root(target: Path) -> Path:
    return (target if target.is_dir() else target.parent).resolve()


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


def _select_entrypoints(
    target: Path,
    tex_files: list[Path],
    parsed_cache: dict[Path, ParsedTex],
    findings: list[Finding],
) -> list[Path]:
    if target.is_file():
        return [target.resolve()]

    roots: list[Path] = []
    unreadable: set[Path] = set()

    for path in tex_files:
        try:
            parsed = parse_tex(path)
        except (OSError, UnicodeError):
            unreadable.add(path)
            continue
        parsed_cache[path] = parsed
        if parsed.has_documentclass:
            roots.append(path)

    if roots:
        return sorted(roots)

    readable = [path for path in tex_files if path not in unreadable]
    if len(readable) == 1:
        return readable

    if readable:
        findings.append(
            Finding(
                path=target,
                severity=Severity.INFO,
                code="ENTRYPOINT_UNKNOWN",
                message=(
                    "No LaTeX file with \\documentclass was found; "
                    "all readable .tex files will be treated as entry points."
                ),
            )
        )
    return readable


def _reachable_sources(
    roots: list[Path],
    parsed_cache: dict[Path, ParsedTex],
    findings: list[Finding],
) -> tuple[list[ParsedTex], list[tuple[Path, Path, int]]]:
    queue = list(roots)
    visited: set[Path] = set()
    parsed: list[ParsedTex] = []
    edges: list[tuple[Path, Path, int]] = []

    while queue:
        path = queue.pop(0).resolve()
        if path in visited:
            continue
        visited.add(path)

        source = parsed_cache.get(path)
        if source is None:
            try:
                source = parse_tex(path)
            except (OSError, UnicodeError) as exc:
                findings.append(
                    Finding(
                        path=path,
                        severity=Severity.ERROR,
                        code="TEX_UNREADABLE",
                        message=f"Could not read LaTeX source: {exc}.",
                    )
                )
                continue
            parsed_cache[path] = source

        parsed.append(source)

        for include, line in source.includes:
            resolved = _resolve_source(source, include)
            if resolved is None:
                findings.append(
                    Finding(
                        path=source.path,
                        severity=Severity.ERROR,
                        code="SOURCE_FILE_MISSING",
                        message=f"Included LaTeX source was not found: {include}.",
                        line=line,
                    )
                )
                continue

            edges.append((source.path, resolved, line))
            if resolved not in visited:
                queue.append(resolved)

    return parsed, edges


def _find_include_cycles(
    parsed: list[ParsedTex],
    edges: list[tuple[Path, Path, int]],
) -> list[Finding]:
    adjacency: dict[Path, list[tuple[Path, int]]] = defaultdict(list)
    for source, dest, line in edges:
        adjacency[source].append((dest, line))

    state: dict[Path, int] = {}
    stack: list[Path] = []
    findings: list[Finding] = []
    reported: set[tuple[Path, Path]] = set()

    def visit(node: Path) -> None:
        state[node] = 1
        stack.append(node)
        for dest, line in adjacency.get(node, []):
            if state.get(dest, 0) == 0:
                visit(dest)
            elif state.get(dest) == 1:
                edge = (node, dest)
                if edge in reported:
                    continue
                reported.add(edge)
                try:
                    start = stack.index(dest)
                    cycle = stack[start:] + [dest]
                except ValueError:
                    cycle = [node, dest]
                findings.append(
                    Finding(
                        path=node,
                        severity=Severity.WARNING,
                        code="INCLUDE_CYCLE",
                        message="LaTeX include cycle detected: "
                        + " -> ".join(path.name for path in cycle)
                        + ".",
                        line=line,
                    )
                )
        stack.pop()
        state[node] = 2

    for source in parsed:
        if state.get(source.path, 0) == 0:
            visit(source.path)

    return findings


def _unused_figure_findings(root: Path, referenced_graphics: set[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for directory in root.rglob("*"):
        if not directory.is_dir() or directory.name.lower() not in _FIGURE_DIR_NAMES:
            continue
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in _IMAGE_EXTENSIONS:
                continue
            resolved = path.resolve()
            if resolved not in referenced_graphics:
                findings.append(
                    Finding(
                        path=path,
                        severity=Severity.INFO,
                        code="FIGURE_UNUSED",
                        message=(
                            "Figure-like file is in a conventional figure directory "
                            "but is not referenced by the reachable manuscript."
                        ),
                    )
                )
    return findings


def inspect_project(target: Path) -> tuple[list[Finding], int, set[Path], set[Path]]:
    """Inspect the reachable manuscript graph and return findings plus assets."""
    root = project_root(target)
    tex_files = discover_tex_files(target)
    findings: list[Finding] = []

    if not tex_files:
        return (
            [Finding(target, Severity.ERROR, "NO_TEX_FILES", "No LaTeX .tex files were found.")],
            0,
            set(),
            set(),
        )

    parsed_cache: dict[Path, ParsedTex] = {}
    roots = _select_entrypoints(target, tex_files, parsed_cache, findings)
    parsed, edges = _reachable_sources(roots, parsed_cache, findings)
    findings.extend(_find_include_cycles(parsed, edges))

    labels: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    refs: list[tuple[str, Path, int]] = []
    cites: list[tuple[str, Path, int]] = []
    nocites: list[tuple[str, Path, int]] = []
    referenced_graphics: set[Path] = set()
    bib_files: set[Path] = set()

    for source in parsed:
        for label, line in source.labels:
            labels[label].append((source.path, line))
        refs.extend((ref, source.path, line) for ref, line in source.refs)
        cites.extend((cite, source.path, line) for cite, line in source.cites)
        nocites.extend((cite, source.path, line) for cite, line in source.nocites)

        for graphic, line in source.graphics:
            resolved = _resolve_graphic(source, graphic, root)
            if resolved is None:
                findings.append(
                    Finding(
                        source.path,
                        Severity.ERROR,
                        "FIGURE_FILE_MISSING",
                        f"Referenced figure file was not found: {graphic}.",
                        line,
                    )
                )
            else:
                referenced_graphics.add(resolved)

        for bibliography, line in source.bibliographies:
            resolved = _resolve_bibliography(source, bibliography, root)
            if resolved is None:
                findings.append(
                    Finding(
                        source.path,
                        Severity.ERROR,
                        "BIB_FILE_MISSING",
                        f"Referenced BibTeX file was not found: {bibliography}.",
                        line,
                    )
                )
            else:
                bib_files.add(resolved)

        for line in source.figure_without_caption_lines:
            findings.append(
                Finding(
                    source.path,
                    Severity.WARNING,
                    "FIGURE_CAPTION_MISSING",
                    "Figure environment has no caption.",
                    line,
                )
            )
        for line in source.table_without_caption_lines:
            findings.append(
                Finding(
                    source.path,
                    Severity.WARNING,
                    "TABLE_CAPTION_MISSING",
                    "Table environment has no caption.",
                    line,
                )
            )
        for line in source.todo_lines:
            findings.append(
                Finding(
                    source.path,
                    Severity.WARNING,
                    "TODO_LEFT",
                    "TODO/FIXME marker remains in manuscript text.",
                    line,
                )
            )

    for label, locations in sorted(labels.items()):
        if len(locations) >= 2:
            location_text = ", ".join(f"{p.name}:{line}" for p, line in locations)
            first_path, first_line = locations[0]
            findings.append(
                Finding(
                    first_path,
                    Severity.ERROR,
                    "LABEL_DUPLICATE",
                    f"Label '{label}' is defined more than once ({location_text}).",
                    first_line,
                )
            )

    defined = set(labels)
    for ref, path, line in refs:
        if ref not in defined:
            findings.append(
                Finding(
                    path,
                    Severity.ERROR,
                    "REF_UNRESOLVED",
                    f"Reference points to undefined label: {ref}.",
                    line,
                )
            )

    cited_keys = {cite for cite, _, _ in cites if cite != "*"}
    nocited_keys = {cite for cite, _, _ in nocites if cite != "*"}
    nocite_all = any(cite == "*" for cite, _, _ in nocites)

    if cites or nocites:
        if not bib_files:
            first = cites[0] if cites else nocites[0]
            findings.append(
                Finding(
                    first[1],
                    Severity.INFO,
                    "BIB_LIBRARY_UNKNOWN",
                    "Citations were found, but no existing BibTeX library was resolved "
                    "from \\bibliography or \\addbibresource.",
                    first[2],
                )
            )
        else:
            bib_entries: dict[str, tuple[Path, int]] = {}
            for bib_path in bib_files:
                for key, line in parse_bib_entries(bib_path).items():
                    bib_entries.setdefault(key, (bib_path, line))

            for cite, path, line in cites + nocites:
                if cite != "*" and cite not in bib_entries:
                    findings.append(
                        Finding(
                            path,
                            Severity.ERROR,
                            "CITATION_MISSING",
                            f"Citation key is missing from BibTeX libraries: {cite}.",
                            line,
                        )
                    )

            if not nocite_all:
                used_keys = cited_keys | nocited_keys
                for key in sorted(set(bib_entries) - used_keys):
                    bib_path, line = bib_entries[key]
                    findings.append(
                        Finding(
                            bib_path,
                            Severity.INFO,
                            "REFERENCE_UNUSED",
                            f"BibTeX entry is not cited by the reachable manuscript: {key}.",
                            line,
                        )
                    )

    findings.extend(_unused_figure_findings(root, referenced_graphics))
    return findings, len(parsed), referenced_graphics, bib_files

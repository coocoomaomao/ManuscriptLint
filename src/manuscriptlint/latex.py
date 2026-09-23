from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


_LABEL_RE = re.compile(r"\\label\s*\{([^{}]+)\}")
_REF_RE = re.compile(r"\\(?:ref|eqref|autoref|pageref)\s*\{([^{}]+)\}")
_CITE_RE = re.compile(
    r"\\(?:cite|citep|citet|parencite|textcite|autocite)"
    r"(?:\s*\[[^\]]*\]){0,2}\s*\{([^{}]+)\}"
)
_NOCITE_RE = re.compile(r"\\nocite\s*\{([^{}]+)\}")
_GRAPHIC_RE = re.compile(r"\\includegraphics(?:\s*\[[^\]]*\])?\s*\{([^{}]+)\}")
_INCLUDE_RE = re.compile(r"\\(?:input|include|subfile)\s*\{([^{}]+)\}")
_BIBLIOGRAPHY_RE = re.compile(r"\\bibliography\s*\{([^{}]+)\}")
_ADDBIB_RE = re.compile(
    r"\\addbibresource(?:\s*\[[^\]]*\])?\s*\{([^{}]+)\}"
)
_GRAPHICSPATH_RE = re.compile(r"\\graphicspath\s*\{((?:\{[^{}]*\}\s*)+)\}")
_DOCUMENTCLASS_RE = re.compile(r"\\documentclass(?:\s*\[[^\]]*\])?\s*\{")
_TODO_RE = re.compile(r"\b(?:TODO|FIXME)\b", re.IGNORECASE)
_BIB_KEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedTex:
    path: Path
    text: str
    labels: list[tuple[str, int]]
    refs: list[tuple[str, int]]
    cites: list[tuple[str, int]]
    nocites: list[tuple[str, int]]
    graphics: list[tuple[str, int]]
    includes: list[tuple[str, int]]
    bibliographies: list[tuple[str, int]]
    graphicspaths: list[str]
    figure_without_caption_lines: list[int]
    table_without_caption_lines: list[int]
    todo_lines: list[int]
    has_documentclass: bool


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def strip_comments(text: str) -> str:
    """Remove unescaped LaTeX comments while preserving line numbers."""
    out: list[str] = []
    for line in text.splitlines(keepends=True):
        cut = None
        for idx, char in enumerate(line):
            if char != "%":
                continue
            backslashes = 0
            pos = idx - 1
            while pos >= 0 and line[pos] == "\\":
                backslashes += 1
                pos -= 1
            if backslashes % 2 == 0:
                cut = idx
                break
        if cut is None:
            out.append(line)
        else:
            ending = "\n" if line.endswith("\n") else ""
            out.append(line[:cut] + ending)
    return "".join(out)


def _matches(pattern: re.Pattern[str], text: str) -> list[tuple[str, int]]:
    return [(m.group(1).strip(), _line_number(text, m.start())) for m in pattern.finditer(text)]


def _split_multi(values: list[tuple[str, int]]) -> list[tuple[str, int]]:
    result: list[tuple[str, int]] = []
    for raw, line in values:
        for item in raw.split(","):
            item = item.strip()
            if item:
                result.append((item, line))
    return result


def _missing_captions(text: str, environment: str) -> list[int]:
    pattern = re.compile(
        rf"\\begin\{{{environment}\*?\}}(.*?)\\end\{{{environment}\*?\}}",
        re.DOTALL,
    )
    lines: list[int] = []
    for match in pattern.finditer(text):
        body = match.group(1)
        if not re.search(r"\\caption(?:\s*\[[^\]]*\])?\s*\{", body):
            lines.append(_line_number(text, match.start()))
    return lines


def parse_tex(path: Path) -> ParsedTex:
    text = path.read_text(encoding="utf-8")
    clean = strip_comments(text)

    graphicspaths: list[str] = []
    for match in _GRAPHICSPATH_RE.finditer(clean):
        graphicspaths.extend(
            item.strip()
            for item in re.findall(r"\{([^{}]*)\}", match.group(1))
            if item.strip()
        )

    return ParsedTex(
        path=path.resolve(),
        text=clean,
        labels=_matches(_LABEL_RE, clean),
        refs=_matches(_REF_RE, clean),
        cites=_split_multi(_matches(_CITE_RE, clean)),
        nocites=_split_multi(_matches(_NOCITE_RE, clean)),
        graphics=_matches(_GRAPHIC_RE, clean),
        includes=_matches(_INCLUDE_RE, clean),
        bibliographies=_split_multi(_matches(_BIBLIOGRAPHY_RE, clean))
        + _matches(_ADDBIB_RE, clean),
        graphicspaths=graphicspaths,
        figure_without_caption_lines=_missing_captions(clean, "figure"),
        table_without_caption_lines=_missing_captions(clean, "table"),
        todo_lines=[_line_number(clean, m.start()) for m in _TODO_RE.finditer(clean)],
        has_documentclass=bool(_DOCUMENTCLASS_RE.search(clean)),
    )


def discover_tex_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target.resolve()] if target.suffix.lower() == ".tex" else []
    return sorted(path.resolve() for path in target.rglob("*.tex") if path.is_file())


def parse_bib_entries(path: Path) -> dict[str, int]:
    """Return BibTeX entry keys mapped to approximate source line numbers."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return {}
    clean = strip_comments(text)
    return {
        m.group(1).strip(): _line_number(clean, m.start())
        for m in _BIB_KEY_RE.finditer(clean)
    }


def parse_bib_keys(path: Path) -> set[str]:
    return set(parse_bib_entries(path))

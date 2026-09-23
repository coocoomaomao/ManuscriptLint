# ManuscriptLint 🐈‍⬛📝

> **ESLint for academic manuscripts.**

**ManuscriptLint** is an open-source preflight linter for academic manuscripts. It checks a LaTeX project before submission and catches structural problems that are easy to miss during writing.

Part of **喵造实验室 / MeowBuild Lab** and the Academic Lint family:

- **FigureLint** — figure QA
- **RefLint** — reference QA
- **ManuscriptLint** — manuscript preflight

## Current checks

- duplicate LaTeX labels
- unresolved `\\ref{}` / `\\eqref{}` references
- citations missing from BibTeX libraries
- missing `\\input{}` / `\\include{}` source files
- missing `\\includegraphics{}` files
- figure / table environments without captions
- TODO / FIXME markers left in reachable manuscript text
- **entry-point-aware LaTeX include graph**
- include-cycle detection
- unused figure files in conventional figure directories (informational)
- unused BibTeX entries (informational, respects `\\nocite{*}`)
- optional FigureLint and RefLint integration
- JSON output for editor / CI integrations
- native GitHub Actions annotations
- reusable GitHub composite action
- CI-friendly exit codes and strict mode

When a project directory contains a clear `\\documentclass{}` entry point, ManuscriptLint follows its `\\input{}`, `\\include{}`, and `\\subfile{}` graph. Unrelated draft `.tex` files are not treated as active manuscript content.

## Install from source

Requires Python 3.10+.

~~~bash
git clone https://github.com/coocoomaomao/ManuscriptLint.git
cd ManuscriptLint
python -m venv .venv
pip install -e .
~~~

For development:

~~~bash
pip install -e ".[dev]"
pytest
~~~

## Usage

Check one manuscript:

~~~bash
manuscriptlint check paper.tex
~~~

Check a whole LaTeX project:

~~~bash
manuscriptlint check paper/
~~~

Treat warnings as CI failures:

~~~bash
manuscriptlint check paper/ --strict
~~~

Machine-readable JSON:

~~~bash
manuscriptlint check paper/ --format json
~~~

Emit native GitHub workflow annotations:

~~~bash
manuscriptlint check paper/ --github-annotations
~~~

Run the wider Academic Lint toolchain when FigureLint / RefLint are installed:

~~~bash
manuscriptlint check paper/ --figurelint --reflint
~~~

### GitHub Actions

~~~yaml
- uses: coocoomaomao/ManuscriptLint@main
  with:
    path: paper/
    strict: "true"
~~~

See [GitHub Action usage](docs/GITHUB_ACTION.md).

## Philosophy

ManuscriptLint focuses on **deterministic preflight checks**. It should identify verifiable structural problems without pretending to judge scientific quality, novelty, or whether a paper will be accepted.

Unused figures and unused references are currently informational because research repositories often keep intentional extras.

## Planned next

- graphicspath / macro handling improvements
- supplementary-material checks
- source-backed publisher presets
- DOCX manuscript support

## License

MIT

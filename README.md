# ManuscriptLint 🐈‍⬛📝

> **ESLint for academic manuscripts.**

**ManuscriptLint** is an open-source preflight linter for academic manuscripts. It checks a LaTeX project before submission and catches structural problems that are easy to miss during writing.

Part of **喵造实验室 / MeowBuild Lab** and the Academic Lint family:

- **FigureLint** — figure QA
- **RefLint** — reference QA
- **ManuscriptLint** — manuscript preflight

## What v0.1 checks

- duplicate LaTeX labels
- unresolved `\\ref{}` / `\\eqref{}` references
- citations missing from BibTeX libraries
- missing `\\input{}` / `\\include{}` source files
- missing `\\includegraphics{}` files
- figure / table environments without captions
- TODO / FIXME markers left in manuscript text
- recursive LaTeX project discovery
- optional FigureLint and RefLint integration
- CI-friendly exit codes and strict mode

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

Run the wider Academic Lint toolchain when FigureLint / RefLint are installed:

~~~bash
manuscriptlint check paper/ --figurelint --reflint
~~~

## Philosophy

ManuscriptLint focuses on **deterministic preflight checks**. It should identify verifiable structural problems without pretending to judge scientific quality, novelty, or whether a paper will be accepted.

## Planned next

- smarter LaTeX include graph
- cross-file figure/table numbering diagnostics
- supplementary-material checks
- JSON output and native GitHub annotations
- source-backed publisher presets
- DOCX manuscript support

## License

MIT

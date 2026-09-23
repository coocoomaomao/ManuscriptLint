# Changelog

All notable changes to ManuscriptLint will be documented in this file.

## [Unreleased]

### Planned
- graphicspath / macro-resolution improvements
- supplementary-material checks
- source-backed publisher submission profiles
- DOCX support where deterministic checks are practical

## [0.1.0] - 2026-09-23

### Added
- initial ManuscriptLint CLI
- recursive LaTeX project discovery
- duplicate-label detection
- unresolved-reference detection
- missing citation-key checks
- missing figure/source/BibTeX file checks
- figure/table caption checks
- TODO/FIXME checks
- optional FigureLint and RefLint integration
- strict mode and CI-ready exit codes
- Python 3.10–3.12 CI
- entry-point-aware LaTeX include graph
- include-cycle detection
- informational unused-figure diagnostics
- informational unused-BibTeX-entry diagnostics
- `\\nocite{*}` handling for unused-reference checks
- machine-readable JSON output
- native GitHub Actions workflow annotations
- reusable composite GitHub Action
- wheel / sdist build validation
- PyPI Trusted Publishing workflow

[Unreleased]: https://github.com/coocoomaomao/ManuscriptLint/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/coocoomaomao/ManuscriptLint/releases/tag/v0.1.0

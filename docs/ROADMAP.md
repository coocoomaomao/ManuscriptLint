# Roadmap

## v0.1 — LaTeX submission preflight
- labels and references
- citations and BibTeX libraries
- figure file resolution
- included source-file resolution
- caption checks
- TODO / FIXME checks
- explicit FigureLint / RefLint integration
- recursive project scanning
- CI-friendly exit codes

## v0.2 — project intelligence
- [x] smarter LaTeX include graph
- [x] include-cycle detection
- [x] unused figures in conventional figure directories
- [x] unused BibTeX references
- [ ] graphicspath / macro handling improvements
- [ ] supplementary-material checks
- [ ] JSON output
- [ ] native GitHub annotations

## v0.3 — submission profiles
- source-backed publisher presets
- manuscript-package naming rules
- reproducibility / artifact manifests
- DOCX support where checks can be made reliably

## Long term
ManuscriptLint is the project-level coordinator for the Academic Lint family: FigureLint handles figures, RefLint handles bibliographic data, and ManuscriptLint checks how the submission package fits together.

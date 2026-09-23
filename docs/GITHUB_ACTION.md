# GitHub Action

ManuscriptLint can run directly in GitHub Actions and emit native workflow annotations on the affected LaTeX files and lines.

## Basic use

Until the first tagged release is published, use `@main`:

~~~yaml
name: Manuscript Preflight

on:
  pull_request:
  push:
    branches: [main]

jobs:
  manuscript:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: coocoomaomao/ManuscriptLint@main
        with:
          path: paper/
          strict: "true"
~~~

After a tagged release, pin the action to a release tag instead of `@main`.

## Run the whole Academic Lint family

~~~yaml
- uses: coocoomaomao/ManuscriptLint@main
  with:
    path: paper/
    figurelint: "true"
    reflint: "true"
~~~

When enabled, the action installs the public FigureLint and RefLint packages before running the project preflight.

## Annotation mapping

| ManuscriptLint severity | GitHub annotation |
| --- | --- |
| error | error |
| warning | warning |
| info | notice |

## Direct CLI use

~~~bash
manuscriptlint check paper/ --github-annotations
~~~

Use `--strict` if warnings should fail the workflow.

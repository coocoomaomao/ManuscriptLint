# Contributing

Thanks for helping improve ManuscriptLint.

## Development

~~~bash
python -m venv .venv
pip install -e ".[dev]"
pytest
~~~

When adding a rule:
- prefer deterministic checks over guesses,
- add a focused fixture/test,
- document known false-positive risks,
- avoid claims about scientific quality or acceptance likelihood.

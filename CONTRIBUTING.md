# Contributing to partialjson

Thanks for your interest in contributing! This project welcomes bug reports, feature requests, and pull requests.

## Getting started

- Fork and clone the repository
- Create a virtual environment and install dependencies
- Run tests to ensure a clean baseline

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
pytest -q
```

## Development workflow

- Create a feature branch from `main`
- Add tests for new behavior
- Run `pytest` locally and ensure all tests pass
- Submit a pull request with a clear description and motivation

## Code style

- Prefer small, readable functions and clear naming
- Add focused docstrings where non-obvious decisions are made
- Keep public API changes minimal and documented in `CHANGELOG.md`

## Reporting issues

Please include:

- Expected behavior and what happened instead
- Minimal reproducible example
- Environment details (Python version, OS)

Thank you for helping improve partialjson!

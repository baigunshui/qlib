# Repository Guidelines

## Project Structure & Module Organization
`qlib/` contains the Python package, including core domains such as `data/`, `model/`, `backtest/`, `strategy/`, `workflow/`, and `rl/`. Put library code here and keep public APIs aligned with existing module boundaries. `tests/` mirrors major package areas with suites like `tests/backtest/`, `tests/model/`, `tests/rl/`, and `tests/dataset_tests/`. `examples/` holds runnable workflows and benchmark configs, while `scripts/` contains data utilities and collectors. `docs/` contains Sphinx sources and developer guidance.

## Build, Test, and Development Commands
Use the existing `Makefile` targets instead of ad hoc setup:

- `make install`: build required Cython extensions and install the package.
- `make dev`: install the full development stack, including lint, docs, test, and RL extras.
- `pytest tests`: run the default test suite.
- `pytest tests -m "not slow"`: skip tests marked `slow`.
- `make lint`: run `black`, `pylint`, `flake8`, `mypy`, and `nbqa`.
- `make docs-gen`: build Sphinx docs into `public/`.

## Coding Style & Naming Conventions
Target Python `>=3.8` and follow existing package patterns. Use 4-space indentation, `snake_case` for functions/modules, `PascalCase` for classes, and keep constants uppercase. Format code with `black -l 120`; the repo also enforces `flake8` and `pylint`. Docstrings should use Numpydoc style, per `docs/developer/code_standard_and_dev_guide.rst`. When adding notebooks, ensure they pass `nbqa`.

## Testing Guidelines
Write tests under the matching `tests/` subdirectory and name files `test_*.py`. Prefer focused unit tests near the affected subsystem, then extend integration coverage only when behavior crosses module boundaries. Reuse existing pytest markers and fixtures from `tests/conftest.py`. If a change touches optional components such as RL, storage, or data collectors, run the most relevant targeted suite before submitting.

## Commit & Pull Request Guidelines
Commit and PR titles follow Conventional Commits and are checked by `commitlint`. Use types from `.commitlintrc.js`, such as `feat`, `fix`, `docs`, `refactor`, `test`, or `ci`; keep the header under 100 characters. Recent history shows the expected style, for example: `fix(backtest): avoid calendar overflow when end_time is missing`. Before opening a PR, run `make lint` and the relevant `pytest` command, summarize behavior changes, and link related issues. Include screenshots only when updating docs or visual outputs.

## Contributor Workflow Tips
Install hooks with `pre-commit install` after `pip install -e .[dev]`. Avoid unrelated refactors in large modules; this repository spans research, data, and trading workflows, so small scoped changes review more cleanly.

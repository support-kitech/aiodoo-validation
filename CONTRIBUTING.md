# Contributing to aiodoo-validation

Thank you for contributing to the AIODOO ecosystem.

## Development setup

```bash
python3 -m pip install -r requirements/dev.txt
```

## Quality checks (match CI)

```bash
ruff check .
ruff format --check .
mypy aiodoo_validation
coverage run -m pytest
coverage report -m --fail-under=85
```

## Architecture rules

- **Validation only** — do not add training, dataset generation, registry, or agent runtime code.
- Follow the **frozen Implementation Plan** — implement only the active phase unless explicitly approved.
- Domain objects are **immutable** frozen dataclasses.
- Engine boundaries from the frozen TDD must be preserved.

## Pull requests

Use the PR template checklist. Every PR must state which implementation phase it belongs to.

## ADRs

Use [docs/adr/0000-adr-template.md](docs/adr/0000-adr-template.md) for irreversible decisions.

## Issues

Use GitHub issue templates for bugs and feature requests. Features must align with frozen architecture.

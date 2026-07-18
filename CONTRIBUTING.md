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

- **Validation only** — do not add training, dataset generation, model registry, or agent runtime code.
- This repository is in **permanent maintenance mode for v1.0.x** — see [docs/MAINTENANCE.md](docs/MAINTENANCE.md).
- Allowed: bug fixes, security fixes, documentation, capability pack registration without core redesign.
- Forbidden: new features, architecture changes, new profiles, non-repair behavioral capability delivery.
- Domain objects are **immutable** frozen dataclasses.
- Engine boundaries from the frozen Protocol V1 lifecycle must be preserved.

## Pull requests

Use the PR template checklist. Every PR must state whether it is a
**maintenance** change (bug/security/docs/pack registration) and must not
reopen frozen Capability Delivery architecture.

## ADRs

Use [docs/adr/0000-adr-template.md](docs/adr/0000-adr-template.md) for irreversible decisions.

## Issues

Use GitHub issue templates for bugs and feature requests. Features must align with frozen architecture.

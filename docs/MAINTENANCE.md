# Maintenance Policy (v2.0.x)

**Status:** Maintenance mode for the **v2.0.x** series after the **v2.0.0**
source / git-tag release (AIODOO ecosystem tooling alignment).

Validation **Protocol V1** and Capability Delivery **E0–E8** remain
architecturally frozen. This major bumps **repository / release identity** and
release honesty (gitignore, docs); it does **not** introduce Protocol V2.

This repository is **frozen infrastructure**, not a feature delivery track.

## Allowed changes (v2.0.x)

- Bug fixes that restore documented contracts
- Security fixes
- Documentation corrections and clarifications
- Test coverage for existing behavior
- Future **capability pack registrations** that plug into the existing
  `CapabilityRegistry` / pack contract **without** changing Protocol V1,
  the ValidationEngine lifecycle, or public API shapes

## Forbidden changes (v2.0.x)

- Architecture redesigns (engine, runners, pipelines, corpus loader core)
- New top-level Protocol stages or CLI redesign
- New adapter profiles (e.g. `merged`, `foundation`, `context`) unless an
  explicit ADR extends the frozen seven-profile set
- Refactors that alter public identifiers, stage IDs, or result shapes
- PyPI `[build-system]` packaging (source-tag distribution remains policy)

## Compatibility guarantee

For **v2.x** (Protocol major still **1**):

- Symbols exported from `aiodoo_validation.api` (and top-level
  `ValidationService`, `__version__`) remain stable
- Protocol major remains **1**
- Profile names, execution tiers, validation kinds, and published stage /
  oracle / score / benchmark / certification / report identifiers for shipped
  profiles remain stable
- Request metadata keys `evaluation_corpus_id` and `evaluation_corpus_path`
  remain stable

Further breaking Protocol or public-API changes require a new major and an
explicit ADR.

## Distribution

Consumers depend on a **git tag / source checkout** (`PYTHONPATH=.` or
`./scripts/aiodoo-validation`). This repo is intentionally not a PyPI wheel
publisher under current policy.

## Related documents

- [README.md](../README.md)
- [SPECIFICATION_V1.md](SPECIFICATION_V1.md)
- [AUDIT_RESOLUTION.md](../AUDIT_RESOLUTION.md)
- [IMPLEMENTATION_REPORT.md](../IMPLEMENTATION_REPORT.md)

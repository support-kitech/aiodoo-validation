# Maintenance Policy (v1.0.x)

**Status:** Permanent maintenance mode for the **v1.0.x** series after the
**v1.0.0** source / git-tag release.

This repository is **frozen infrastructure**, not a feature delivery track.

## Allowed changes (v1.0.x)

- Bug fixes that restore documented contracts
- Security fixes
- Documentation corrections and clarifications
- Test coverage for existing behavior
- Future **capability pack registrations** that plug into the existing
  `CapabilityRegistry` / pack contract **without** changing Protocol V1,
  the ValidationEngine lifecycle, or public API shapes

## Forbidden changes (v1.0.x)

- Architecture redesigns (engine, runners, pipelines, corpus loader core)
- New top-level Protocol stages or CLI redesign
- New adapter profiles (e.g. `merged`, `foundation`)
- New behavioral validation for execution /
  approval / evaluation (Repair, Coding, Planner, and Conversation reuse the
  frozen spine)
- Refactors that alter public identifiers, stage IDs, or result shapes
- PyPI `[build-system]` packaging (source-tag distribution remains policy)

## Compatibility guarantee

For **v1.x**:

- Symbols exported from `aiodoo_validation.api` (and top-level
  `ValidationService`, `__version__`) remain stable
- Protocol major remains **1**
- Profile names, execution tiers, validation kinds, and published stage /
  oracle / score / benchmark / certification / report identifiers for shipped
  profiles remain stable
- Request metadata keys `evaluation_corpus_id` and `evaluation_corpus_path`
  remain stable

Breaking changes require a **v2.0.0** major and an explicit ADR.

## Distribution

Consumers depend on a **git tag / source checkout** (`PYTHONPATH=.` or an
install path that works without inventing a wheel build system). This repo is
intentionally not a PyPI wheel publisher under current policy.

## Related documents

- [implementation_status.md](implementation_status.md)
- [delivery_governance.md](delivery_governance.md)
- [integration.md](integration.md)
- [CHANGELOG.md](../CHANGELOG.md)

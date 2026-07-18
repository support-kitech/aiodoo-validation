# Changelog

All notable changes to **aiodoo-validation** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Notes

No unreleased changes after the v1.0.0 release candidate cut.

## [1.0.0] — 2026-07-18

### Overview

First official **v1.0.0** release of **AIODOO Validation**.

Validation Protocol V1 is complete and architecturally frozen. Capability
Delivery phases E0–E8 are complete and frozen. Production hardening (R1) and
release-candidate validation (RC1) are complete.

**Distribution model:** this repository is a **source / git-tag release**.
`pyproject.toml` is intentionally tooling-oriented (no `[build-system]`);
consumers use a checkout with `PYTHONPATH=.` or an editable install from source.
PyPI wheel publishing is out of scope for this release policy.

### Added

- Capability Delivery E0–E8 (domain, corpus, transforms, BehaviorCaseBuilder,
  Repair pack, production behavior wiring, behavioral scoring, corpus pinning,
  behavior-gated certification)
- R1 production hardening (shared domain freeze helper, scoring layering cleanup,
  wiring consistency tests)
- RC1 release validation (CI format gate green; packaging policy documented)

### Changed

- Production path is structural oracles/scoring/benchmark/certification/reports
  (not placeholder-only for the default CLI/production stack)
- Repair profile includes behavior oracle → score → benchmark → certification →
  report chain when evaluation corpus id/path is configured
- [implementation_status.md](docs/implementation_status.md) and README reflect
  Spec v1.0 + E0–E8 + R1/RC1

### Compatibility

- Public CLI and Validation Protocol V1 stage order unchanged
- `prod` remains an alias of `full`
- Public API: `aiodoo_validation.api` symbols stable for v1.x
- Stub/placeholder modules retained for `create_with_stubs()` only
- Python >= 3.12

### Known limitations (intentional)

- Behavioral corpora: prefer `evaluation_corpus_id`; path accepted; deferred if unset
- Behavior-gated certification enabled for **repair** only
- Semantic / AI similarity comparators deferred
- Artifact content fingerprints remain placeholder digests
- PDF/HTML/Markdown report rendering deferred to consumers
- `merged` / `foundation` profiles unsupported
- No PyPI `[build-system]` packaging (source-tag distribution)

### Public API

Stable symbols from `aiodoo_validation.api` (v1.x guarantee):

- `ValidationService`, `build_coding_request`, `parse_odoo_versions`
- `get_repository_metadata`, `ProtocolInfo`, `RepositoryMetadata`
- `list_profiles`, `get_profile_info`, `ProfileInfo`, `capability_labels`
- Compatibility helpers and result helpers
- Integration hints (`training_integration_hints`, …)

Top-level: `ValidationService`, `__version__` (`1.0.0`).

### CLI

| Command | Description |
|---------|-------------|
| `validate` | Full validation lifecycle |
| `version` | Repository and protocol version |
| `capabilities` | Profiles and pipeline stages |
| `help` | Usage |

Entry points from a source checkout: `python3 -m aiodoo_validation` and, when
the console script is installed from source, `aiodoo-validation`.

---

## Release history

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | 2026-07-18 | Protocol V1 + Capability Delivery E0–E8; source-tag release |

# Changelog

All notable changes to **aiodoo-validation** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Notes

Coding Profile Completion **Phase 2 — Behavioral Validation Pipeline** landed:
Coding reuses the Repair Capability Delivery spine (behavior oracle, scoring,
benchmark, certification, reports, corpus pins) with Coding-specific IDs,
pack/parser, fixture corpus, and production registration.

Phase 1 foundation (Capability Pack / parser / registration) remains in place.

Post-tag v1.0.x changes otherwise remain limited to maintenance (bugs, security,
docs, pack registration). See [docs/MAINTENANCE.md](docs/MAINTENANCE.md).

### Added

- Coding behavioral pipeline stages on `CodingProfile` (oracle→score→bench→cert→report)
- Coding evaluation corpus fixture + pin (`fixture.coding.eval.behavior`, aliases `coding.eval`)
- `BehavioralEvidenceScorePolicy.create_for_coding()` / `BehaviorGatedCertificationPolicy.create_for_coding()`
- Production registration of Coding capability behavioral oracle alongside Repair
- Integration tests: `tests/integration/test_coding_behavior_pipeline.py`

### Changed

- `capabilities/bootstrap` / production DI register Coding behavior with Repair
- Corpus catalog includes Coding fixture pin and capability default
- Coding plan builder resolves evaluation corpus configuration like Repair
- Docs: `coding_profile.md`, `implementation_status.md`, `MAINTENANCE.md`

## [1.0.0] — 2026-07-18

### Overview

First official **v1.0.0** release of **AIODOO Validation**.

Validation Protocol V1 is complete and architecturally frozen. Capability
Delivery phases E0–E8 are complete and frozen. Production hardening (R1),
release-candidate validation (RC1), and the final release audit (RC2) are
complete. The repository enters **permanent maintenance mode** for **v1.0.x**.

**Distribution model:** this repository is a **source / git-tag release**.
`pyproject.toml` is intentionally tooling-oriented (no `[build-system]`);
consumers use a checkout with `PYTHONPATH=.` (preferred) or another source
install path. PyPI wheel publishing is out of scope for this release policy.

### Added

- Capability Delivery E0–E8 (domain, corpus, transforms, BehaviorCaseBuilder,
  Repair pack, production behavior wiring, behavioral scoring, corpus pinning,
  behavior-gated certification)
- R1 production hardening (shared domain freeze helper, scoring layering cleanup,
  wiring consistency tests)
- RC1 release validation (CI format gate green; packaging policy documented)
- RC2 final release audit (contract freeze, maintenance policy, GO for git tag)

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
| 1.0.0 | 2026-07-18 | Protocol V1 + E0–E8; R1/RC1/RC2; source-tag; v1.0.x maintenance |

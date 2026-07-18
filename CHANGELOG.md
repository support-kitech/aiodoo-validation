# Changelog

All notable changes to **aiodoo-validation** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- E7 evaluation corpus governance: `CorpusPin` / `CorpusPinRegistry`,
  `ProductionCorpusLookup`, `evaluation_corpus_id` plan resolution,
  builtin repair fixture pin, pin verification after load, unit tests in
  `tests/unit/test_e7_corpus_governance.py`, integration test in
  `tests/integration/test_e7_corpus_pinning.py`
- E6 behavioral scoring integration: `scoring.evidence` metadata interpretation,
  `scoring.policy_loader` / `scoring.policy_defaults` for
  `default_scoring_policy_ref`, `BehavioralEvidenceScorePolicy`
  (`repair.score.behavior`), multi-dimension aggregation via
  `behavior_dimensions_from_evidence`, repair scoring pipeline stage, unit
  tests in `tests/unit/test_e6_behavioral_scoring.py`
- E5 production behavioral wiring: generic `CapabilityRegistry` /
  `RegisteredCapabilityPack`, `ConfigurableCorpusProvider`,
  `CapabilityBehaviorPipeline`, `CapabilityBehavioralOracle`, repair-only
  registration in `production.py`, repair plan behavior stage, request metadata
  key `evaluation_corpus_path`, integration tests under
  `tests/integration/test_e5_production_behavior_wiring.py`
- E4 Repair Capability Pack (`aiodoo_validation.capabilities.repair`):
  `RepairRecordParser`, `RepairCapabilityPack` / `get_repair_capability_pack`,
  `build_repair_specification`, declarative `capability.yaml`, fixtures under
  `tests/fixtures/capabilities/repair/`
- E3 BehaviorCaseBuilder (`aiodoo_validation.behavior.case_builder`):
  `BehaviorCaseBuilder`, `BehaviorCaseBuildResult`,
  `descriptor_to_replace_transformation`, `BehaviorCaseBuildError`
- E2 transforms package (`aiodoo_validation.transforms`): `ArtifactSnapshot`,
  `ReplaceTransformation`, `TransformationResult`, `TransformationEngine`,
  `SnapshotComparator` / `SnapshotComparisonResult` (delegates to comparator
  framework), transformation exceptions
- E1 corpus package (`aiodoo_validation.corpus`): `JsonlCorpusLoader`,
  `LoadedCorpus`, manifest parsing, JSONL loading, fingerprinting, fail-closed
  gates (`evaluate_corpus_manifest` / `require_corpus_manifest`), corpus
  exceptions, and unit fixtures under `tests/fixtures/corpus/`
- E0 domain foundation: `CorpusRole`, `CorpusManifest`, `CapabilitySpecification`,
  `CorpusRequirements`, `RuntimeRequirements`, `ParsedCapabilityRecord`,
  `CapabilityArtifact`, `TransformationDescriptor`
- E0.3 identity alignment: `CorpusManifest.capability_id` (was `profile_name`)
- Spec Version 1.0 documentation freeze: [SPECIFICATION_V1.md](docs/SPECIFICATION_V1.md),
  [capability_validation_contract.md](docs/capability_validation_contract.md),
  [capability_specification.md](docs/capability_specification.md),
  [engineering_execution_plan.md](docs/engineering_execution_plan.md),
  [delivery_governance.md](docs/delivery_governance.md)
- Historical banners / cross-links for Artifact Resolution vs Capability Delivery naming
- Deterministic comparators: AST, XML, JSON, token similarity (no AI)
- Behavioral validation architecture (`domain.behavior`, `behavior.BehaviorRunner`,
  `oracles.behavioral`) — prompt → inference → comparator → score hooks
- Comparator framework registry with semantic/rule deferred stubs
- Score dimensions architecture (`scoring.dimensions`)
- Reusable certification criteria (`certification.criteria`)
- Richer production reports with structural/behavior/score/benchmark/certification
  summaries and machine-readable `run_summary`
- Optional `RuntimeBenchmarkMetadata` schema for future runtime metrics
- `BehaviorStatus` enum; production reports `deferred` without corpora
- Expanded `ComparatorCapability` descriptive flags
- Version/kind certification label helpers (`certification_label_versioned`,
  `certification_label_kind`) — CLI still uses stable `certification_label()`
- Docs: [behavioral_validation.md](docs/behavioral_validation.md),
  [extensibility_refinements.md](docs/extensibility_refinements.md)
- Hardening / extensibility tests

### Changed

- [implementation_status.md](docs/implementation_status.md) and README reflect Spec v1.0
  and Capability Delivery E0–E8 (E0–E5 frozen; E6 next)
- README and engine docs updated to reflect production structural path (no longer
  claiming placeholder-only oracles/scoring/certification/reports for CLI default)
- Coding profile strategy label: `coding-v1-structural`
- Execution-tier helpers document standard / smoke / full / prod semantics
- Pipeline execution metadata key: `registry_pipeline` (was `placeholder_pipeline`)

### Compatibility

- Public CLI and Validation Protocol V1 stage order unchanged
- `prod` remains an alias of `full`
- Production certification remains structural until behavioral corpora are attached
- Stub/placeholder modules retained for `create_with_stubs()` only

## [1.0.0] — 2026-07-17

### Overview

First official release of **AIODOO Validation** — the canonical evaluation and
certification framework for AIODOO models. Validation Protocol V1 is complete
and architecturally frozen. The repository enters **maintenance mode** after
this release.

### Major architecture

Validation Protocol V1 pipeline (frozen):

```text
ValidationRequest
  → Validation Engine
  → Artifact Resolution
  → Profile Engine
  → Inference Runner
  → Oracle Framework
  → Scoring Engine
  → Benchmark Engine
  → Certification Engine
  → Report Generator
  → ValidationRunResult
```

External consumers integrate via `ValidationService` (`aiodoo_validation.api`).
The CLI consumes the same public API. Dependency direction is one-way: ecosystem
repositories depend on validation; validation depends on nobody.

### Public API

Stable symbols exported from `aiodoo_validation.api` (guaranteed for v1.x):

- `ValidationService` — primary integration entry point
- `build_coding_request`, `parse_odoo_versions` — request builders
- `get_repository_metadata`, `ProtocolInfo`, `RepositoryMetadata` — version metadata
- `list_profiles`, `get_profile_info`, `ProfileInfo`, `capability_labels` — profile discovery
- `is_protocol_supported`, `is_profile_supported`, `is_odoo_version_supported`, `is_execution_tier_supported` — compatibility
- `is_successful`, `is_certified`, `report_execution`, `stage_statuses` — result helpers
- Integration hints: `training_integration_hints`, `colab_integration_hints`, `vscode_integration_hints`, `model_repository_integration_hints`, `summarize_for_promotion`

Top-level re-exports: `ValidationService`, `__version__`.

Internal packages (`engine`, `oracles`, `scoring`, `benchmark`, `certification`,
`reporting`, `profiles`, `validation_plan`, `ports`, `domain`, `stubs`,
`resolution`, `inference`) are **not** part of the compatibility guarantee.

### CLI

Commands:

| Command | Description |
|---------|-------------|
| `validate` | Run the full validation lifecycle |
| `version` | Show repository and protocol version |
| `capabilities` | Show supported profiles and pipeline stages |
| `help` | Show usage information |

Entry points:

- `python -m aiodoo_validation`
- `aiodoo-validation` (console script after `pip install`)

Exit codes: `0` completed, `1` not certified, `2` failed/internal error, `3` invalid request.

### Validation pipeline

- **Profile:** `coding` (only profile in v1.0.0)
- **Supported Odoo versions:** 17, 18, 19
- **Execution tiers:** `smoke`, `standard`, `full`
- **Protocol version:** 1.0
- **Artifact types:** base model, coding adapter, merged model (optional)

### Known limitations

The following are **intentional** in v1.0.0:

- Placeholder Oracle logic (deterministic stub execution)
- Placeholder Scoring (deterministic stub scores)
- Placeholder Benchmark (deterministic stub comparisons)
- Placeholder Certification (deterministic stub decisions)
- Placeholder Reports (immutable report objects; no rendering)
- No PDF, HTML, JSON, or Markdown report rendering
- No Web UI, async execution, plugin system, or distributed execution
- No GPU inference in CI (CPU-only tests; optional Qwen runtime available outside CI)
- No training, dataset generation, model registry, or agent runtime integration

### Breaking changes

None — this is the first stable release.

### Compatibility statement

- **Python:** >= 3.12
- **Public API:** `aiodoo_validation.api` symbols are stable for the v1.x series
- **Protocol:** Validation Protocol V1 (major=1) only
- **Internal modules:** may change without notice; external repositories must not import them

### Future roadmap (post-v1.0.0, maintenance mode)

- Production oracle implementations
- Production scoring policies
- Production benchmark comparisons
- Production certification policies
- Report renderers (JSON, HTML, PDF) as separate consumer integrations
- Additional validation profiles (e.g. planner)
- Ecosystem repository integrations (training, Colab, VS Code, model repository)

---

## Release history

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | 2026-07-17 | Initial stable release; Validation Protocol V1 frozen |

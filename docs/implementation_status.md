# Implementation Status

**Repository version:** 0.0.0-dev  
**Active phases:** Phase 0 + Phase 1 + Phase 2 + Phase 3 (complete)

## Implemented

### Phase 0 — Repository Foundation

- Project structure (`aiodoo_validation` package)
- `pyproject.toml` tooling (Ruff, mypy, pytest, coverage)
- Requirements (`base`, `dev`, optional `inference`)
- CI workflow (GitHub Actions)
- `.editorconfig`, `.gitignore`, Apache 2.0 LICENSE
- CONTRIBUTING, README, architecture summary
- ADR template, issue/PR templates

### Phase 1 — Validation Engine Core

- `ValidationEngine` orchestrator with full lifecycle ordering
- `ValidationRequest` model with validation errors
- `RunContext` immutable run context
- `ValidationRunResult` and exit statuses
- Execution tiers enum (`smoke`, `standard`, `full`)
- Validation Protocol V1 negotiation (major=1)
- Port protocols for all downstream engines
- Stub implementations for all port stages
- `python3 -m aiodoo_validation` development entry (stub run)
- Unit tests: request, context, protocol, lifecycle, repository structure

### Phase 2 — Artifact Resolution

- `ArtifactType`, `FingerprintPolicy`, resolution error codes
- Immutable `ArtifactBundle` and `ArtifactDescriptor`
- `ArtifactResolverPort` with `ArtifactResolutionOutcome`
- `StubArtifactResolver` and `FilesystemArtifactResolver` (DI)
- Placeholder fingerprint provider (`strict` / `warn` / `off`)
- Compatibility validation (coding profile, rejected adapter types, duplicates)
- Engine integration: bundle attached to `RunContext`; graceful failure (no crash)
- `ValidationEngine.with_filesystem()` factory
- Unit tests with fake fixture directories (no real weights/GPU)
- [Artifact Bundle documentation](artifact_bundle.md)

### Phase 3 — Inference Runner

- `InferenceRunnerPort` with initialize / generate / shutdown
- `InferenceSession`, `GenerationRequest`, `InferenceResult`, structured errors
- `ModelRuntimePort` with `MockModelRuntime` (CI default) and `QwenModelRuntime` (optional)
- `RealInferenceRunner` and `StubInferenceRunner` (dependency injection)
- Load lifecycle: initialize → load base → attach adapter → verify → ready
- Generation metadata (tokens, latency, memory placeholder)
- Resource cleanup on shutdown; graceful inference failure in engine
- `ValidationEngine.with_mock_inference()` factory
- Unit tests: mock inference, lifecycle, errors, cleanup (no GPU/downloads)
- [Inference Runner documentation](inference_runner.md)

## Not implemented (next phases)

| Phase | Component |
|-------|-----------|
| 4 | Coding Validation Profile |
| 5 | Oracle Framework |
| 6 | Scoring Engine |
| 7 | Benchmark Engine |
| 8 | Certification Engine |
| 9 | Validation Protocol V1 reports |
| 10 | CLI (`validate`, `certify`, …) |
| 11 | aiodoo-training / Colab integration |
| 12 | Production hardening |
| 13 | v1.0.0 release |

## Next phase

**Phase 4 — Coding Validation Profile** per frozen Implementation Plan.

## Deferred (by design)

| Item | Phase | Reason |
|------|-------|--------|
| Coding profile / validation rules | 4 | Profile engine responsibility |
| Oracles / XML-Python validation | 5 | Oracle framework |
| Scoring / benchmark / certification | 6–8 | Downstream engines |
| Real memory telemetry | Post-3 | Resource layer extension |
| Reports / CLI / Colab | 9–11 | User-facing surfaces |

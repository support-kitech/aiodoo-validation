# AIODOO Validation

**Canonical Evaluation & Certification Framework for AIODOO Models**

Production-grade validation for trained AIODOO adapters and exports. This repository determines whether a trained model is suitable for production — it does **not** train models, generate datasets, manage a model registry, or run AIODOO agents.

## Status

| Phase | Status |
|-------|--------|
| Vision | Frozen |
| Architecture | Frozen |
| Technical Design | Frozen |
| Implementation Plan | Frozen |
| **Phase 0 — Repository Foundation** | **Complete** |
| **Phase 1 — Validation Engine Core** | **Complete** |
| **Phase 2 — Artifact Resolution** | **Complete** |
| **Phase 3 — Inference Runner** | **Complete** |
| **Phase 4 — Coding Validation Profile** | **Complete** |
| **Phase 5 — Oracle Framework** | **Complete** |
| Phase 6+ | Not started |

## Current capabilities (Phase 0–5)

- Production repository foundation (CI, lint, typing, tests, docs)
- **Validation Engine** with full TDD lifecycle ordering (generic orchestration)
- **Artifact Resolution** — filesystem and stub resolvers
- **Coding Validation Profile** — profile selection, compatibility, ValidationPlan
- **Inference Runner** — mock (CI default) and optional Qwen runtime
- **Oracle Framework** — registry + placeholder oracle pipeline execution
- Immutable **RunContext** with artifact bundle, profile, plan, inference session, oracle execution
- Stub ports for scoring, benchmark, certification, report
- Deterministic CPU-only tests — no GPU, no model downloads in CI

## Not yet implemented (deferred by design)

| Component | Implementation Plan phase |
|-----------|---------------------------|
| Real oracle validation rules | Later phases (post placeholder) |
| Scoring Engine | Phase 6 |
| Benchmark Engine | Phase 7 |
| Certification Engine | Phase 8 |
| Reporting / Protocol V1 reports | Phase 9 |
| CLI surface | Phase 10 |
| Ecosystem integration (training, Colab) | Phase 11 |

## Quick start

```bash
python3 -m pip install -r requirements/dev.txt
python3 -m pytest
python3 -m aiodoo_validation   # stub lifecycle run
```

## Scope

**In scope:** validate trained artifacts, emit certification evidence (future), coding profile first.

**Out of scope:** training, dataset generation, model registry, agent runtime, deployment.

## Documentation

- [Architecture summary](docs/architecture.md)
- [Architecture audit (Phase 0–3)](docs/architecture_audit.md)
- [Implementation status](docs/implementation_status.md)
- [Artifact Bundle (Phase 2)](docs/artifact_bundle.md)
- [Inference Runner (Phase 3)](docs/inference_runner.md)
- [Coding Validation Profile (Phase 4)](docs/coding_profile.md)
- [Oracle Framework (Phase 5)](docs/oracle_framework.md)
- [ADR template](docs/adr/0000-adr-template.md)

## License

Apache License 2.0 — see [LICENSE](LICENSE).

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
| Phase 2+ | Not started |

## Current capabilities (Phase 0 + 1)

- Production repository foundation (CI, lint, typing, tests, docs)
- **Validation Engine** skeleton with full TDD lifecycle ordering
- Immutable **ValidationRequest** and **RunContext**
- Validation Protocol V1 negotiation (major version 1 only)
- Stub ports for all downstream engines (artifacts, profile, inference, validation, scoring, benchmark, certification, report)
- Deterministic CPU-only tests — no GPU, no models, no inference

## Not yet implemented (deferred by design)

| Component | Implementation Plan phase |
|-----------|---------------------------|
| Artifact Resolver (real) | Phase 2 |
| Inference Runner | Phase 3 |
| Validation Profiles (coding logic) | Phase 4 |
| Oracle Framework | Phase 5 |
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
- [Implementation status](docs/implementation_status.md)
- [ADR template](docs/adr/0000-adr-template.md)

## License

Apache License 2.0 — see [LICENSE](LICENSE).

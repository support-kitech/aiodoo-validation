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
| **Phase 6 — Scoring Engine** | **Complete / Frozen** |
| **Phase 7 — Benchmark Engine** | **Complete** |
| **Phase 8 — Certification Engine** | **Complete** |
| **Phase 9 — Report Generation** | **Complete** |
| **Phase 10 — Production CLI** | **Complete** |
| **Phase 11 — Ecosystem Integration** | **Complete** |
| Phase 12+ | Not started |

## Current capabilities (Phase 0–11)

- Production repository foundation (CI, lint, typing, tests, docs)
- **Validation Engine** with full TDD lifecycle ordering (generic orchestration)
- **Public Integration API** — `ValidationService`, metadata, builders, helpers
- **Artifact Resolution** — filesystem and stub resolvers
- **Coding Validation Profile** — profile selection, compatibility, ValidationPlan
- **Inference Runner** — mock (CI default) and optional Qwen runtime
- **Oracle Framework** — registry + placeholder oracle pipeline execution
- **Scoring Engine** — consumes oracle results only; placeholder deterministic scores
- **Benchmark Engine** — consumes score results only; placeholder comparisons
- **Certification Engine** — consumes benchmark results only; placeholder certification
- **Report Generator** — consumes certification results only; placeholder report objects
- **Production CLI** — validate, version, capabilities, help; plain terminal output
- Immutable **RunContext** through report execution
- Deterministic CPU-only tests — no GPU, no model downloads in CI

## Not yet implemented (deferred by design)

| Component | Implementation Plan phase |
|-----------|---------------------------|
| Real oracle / scoring / benchmark / certification / report logic | Later phases (post placeholder) |
| PDF / HTML / Markdown / JSON report rendering | Future consumer integrations |
| Production hardening | Phase 12 |

## Public API

```python
from aiodoo_validation.api import ValidationService, build_coding_request

service = ValidationService.create_default()
request = build_coding_request(base_model_ref="./base", adapter_ref="./adapter")
result = service.validate(request)
```

See [Integration guide](docs/integration.md).

## Quick start

```bash
python3 -m pip install -r requirements/dev.txt
python3 -m pytest
python3 -m aiodoo_validation help
aiodoo-validation validate --profile coding --base-model ./base --adapter ./adapter
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
- [Scoring Engine (Phase 6)](docs/scoring_engine.md)
- [Benchmark Engine (Phase 7)](docs/benchmark_engine.md)
- [Certification Engine (Phase 8)](docs/certification_engine.md)
- [Report Generation (Phase 9)](docs/report_generation.md)
- [Production CLI (Phase 10)](docs/cli.md)
- [Ecosystem Integration (Phase 11)](docs/integration.md)
- [ADR template](docs/adr/0000-adr-template.md)

## License

Apache License 2.0 — see [LICENSE](LICENSE).

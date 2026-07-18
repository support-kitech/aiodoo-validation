# AIODOO Validation

**Canonical Evaluation & Certification Framework for AIODOO Models**

Production-grade validation for trained AIODOO adapters and exports. This repository determines whether a trained model is suitable for production — it does **not** train models, generate datasets, manage a model registry, or run AIODOO agents.

**Specification Version 1.0:** start at [docs/SPECIFICATION_V1.md](docs/SPECIFICATION_V1.md).

## Repository Stability

Validation Protocol V1 is **architecturally frozen**.

The stable public API is exposed through `aiodoo_validation.api` and is guaranteed
for the **v1.x** release series.

Internal implementation packages — `engine`, `oracles`, `scoring`, `benchmark`,
`certification`, `reporting`, `profiles`, `validation_plan`, `ports`, `domain`,
`stubs`, `resolution`, `inference`, `behavior`, `comparators`, `corpus`,
`transforms`, `capabilities` — are intentionally excluded from the compatibility
guarantee.

## Status

| Area | Status |
|------|--------|
| Vision / Architecture / TDD | Frozen |
| Validation Protocol V1 pipeline | Frozen |
| Public API + CLI | Frozen |
| Spec v1.0 documentation | Frozen (authoritative in `docs/`) |
| Production structural validation | Active |
| Capability Delivery (EEP E0–E8) | E0–E8 frozen (complete) |
| Production hardening (R1) | Complete |
| Release candidate (RC1) | Complete — source-tag v1.0.0 |
| Behavioral validation | Repair wired (corpus-gated); others deferred |
| **Repository** | Spec synced; structural + repair behavior cert ready for v1.x |

**Repository version:** v1.0.0 (**source / git-tag** release; not a PyPI wheel)

## Current capabilities

- **Validation Engine** — frozen Protocol V1 lifecycle
- **Public Integration API** — `ValidationService`, metadata, builders, helpers
- **CLI** — `validate`, `version`, `capabilities`, `help`
- **Profiles** — coding, planner, repair, conversation, execution, approval, evaluation
- **Execution tiers** — `standard` (never certifies), `smoke`, `full`, `prod`≡`full`
- **Structural / artifact validation** — production oracles on resolved artifacts
- **Scoring / benchmark / certification** — structural policies; repair behavioral scoring (E6) + behavior-gated cert (E8)
- **Corpus governance** — pin by `evaluation_corpus_id` (path is location detail); fingerprint-verified (E7)
- **Profile-aware labels** — e.g. `coding-certified` / `coding-not-certified`
- **Reports** — machine-readable structural/behavior summaries with certification reasons
- **Behavior + comparator architecture** — exact, normalized, AST, XML, JSON, token similarity
- Stub pipeline retained for unit tests (`create_with_stubs`)

## Known limitations (intentional)

| Limitation | Status |
|------------|--------|
| Behavioral evaluation corpora | Prefer `evaluation_corpus_id`; path still accepted; deferred if unset |
| Capability Delivery implementation | E0–E8 complete (see EEP) |
| Semantic / rule-based AI comparators | Deferred (no fake similarity) |
| Behavior-gated certification | **Enabled for repair**; other profiles remain structural-only |
| Content fingerprint hashing | Placeholder digests (artifact resolution era) |
| PDF / HTML / Markdown report rendering | Future consumer integrations |
| `merged` / `foundation` profiles | Intentionally unsupported |
| GPU inference in CI | Not required (CPU-only tests) |
| PyPI wheel packaging | Out of scope — no `[build-system]` by policy |

See [behavioral_validation.md](docs/behavioral_validation.md) for structural vs behavioral honesty.

## Public API

```python
from aiodoo_validation.api import ValidationService, build_coding_request

service = ValidationService.create_default()
request = build_coding_request(
    base_model_ref="./base",
    adapter_ref="./adapter",
    execution_tier="smoke",
    odoo_versions=18,
)
result = service.validate(request)
```

See [Integration guide](docs/integration.md).

## Quick start (source checkout)

```bash
python3 -m pip install -r requirements/dev.txt
export PYTHONPATH=.
python3 -m pytest
python3 -m aiodoo_validation help
python3 -m aiodoo_validation validate \
    --profile coding \
    --base-model ./base \
    --adapter ./adapter \
    --execution-tier smoke \
    --odoo-versions 18
```

Optional inference extras: `pip install -r requirements/inference.txt`.

## Scope

**In scope:** validate trained artifacts, structural certification, repair behavior
evaluation when a corpus is configured, profile-aware evidence.

**Out of scope:** training, dataset generation, model registry, agent runtime,
deployment, invented evaluation corpora, fake semantic scoring, PyPI packaging.

## Documentation

- **[Specification Version 1.0](docs/SPECIFICATION_V1.md)** — start here
- [Capability Validation Contract](docs/capability_validation_contract.md)
- [Capability Specification](docs/capability_specification.md)
- [Engineering Execution Plan](docs/engineering_execution_plan.md)
- [Delivery Governance](docs/delivery_governance.md)
- [Architecture summary](docs/architecture.md)
- [Structural vs Behavioral Validation](docs/behavioral_validation.md)
- [Implementation status](docs/implementation_status.md)
- [Oracle Framework](docs/oracle_framework.md)
- [Scoring Engine](docs/scoring_engine.md)
- [Benchmark Engine](docs/benchmark_engine.md)
- [Certification Engine](docs/certification_engine.md)
- [Report Generation](docs/report_generation.md)
- [Production CLI](docs/cli.md)
- [Ecosystem Integration](docs/integration.md)
- [Changelog](CHANGELOG.md)

## License

Apache License 2.0 — see [LICENSE](LICENSE).

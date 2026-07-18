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
| Release candidate (RC1) | Complete — quality gates + packaging policy |
| Final release audit (RC2) | Complete — infrastructure freeze for v1.0.x |
| Phase 10 consolidation | Complete |
| Phase 11 final release audit | Complete — permanently frozen for v1.x |
| Behavioral validation | All seven profiles wired (corpus-gated; deferred without corpus) |
| **Repository** | **Permanently frozen** for v1.x maintenance (bugs/security/docs only) |

**Repository version:** v1.0.0 (**source / git-tag** release; not a PyPI wheel)

**Maintenance:** v1.0.x accepts bug fixes, security fixes, documentation, and
future capability pack registrations only. Capability Delivery and Protocol V1
are permanently frozen. See [MAINTENANCE.md](docs/MAINTENANCE.md).

## Current capabilities

- **Validation Engine** — frozen Protocol V1 lifecycle
- **Public Integration API** — `ValidationService`, metadata, builders, helpers
- **CLI** — `validate`, `version`, `capabilities`, `help`
- **Profiles** — approval, coding, conversation, evaluation, execution, planner, repair
- **Execution tiers** — `standard` (never certifies), `smoke`, `full`, `prod`≡`full`
- **Structural / artifact validation** — production oracles on resolved artifacts
- **Scoring / benchmark / certification** — structural policies plus behavioral
  scoring (E6) and behavior-gated certification (E8) for all seven profiles
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
| Behavior-gated certification | **Enabled for all seven profiles**; deferred without corpus config |
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

**In scope:** validate trained artifacts, structural certification, behavioral
evaluation for all seven profiles when a corpus is configured, profile-aware
evidence.

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
- [Repair profile](docs/repair_profile.md)
- [Coding profile](docs/coding_profile.md)
- [Planner profile](docs/planner_profile.md)
- [Conversation profile](docs/conversation_profile.md)
- [Execution profile](docs/execution_profile.md)
- [Approval profile](docs/approval_profile.md)
- [Evaluation profile](docs/evaluation_profile.md)
- [Oracle Framework](docs/oracle_framework.md)
- [Scoring Engine](docs/scoring_engine.md)
- [Benchmark Engine](docs/benchmark_engine.md)
- [Certification Engine](docs/certification_engine.md)
- [Report Generation](docs/report_generation.md)
- [Production CLI](docs/cli.md)
- [Ecosystem Integration](docs/integration.md)
- [Maintenance policy (v1.0.x)](docs/MAINTENANCE.md)
- [Changelog](CHANGELOG.md)

## License

Apache License 2.0 — see [LICENSE](LICENSE).

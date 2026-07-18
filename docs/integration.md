# AIODOO Ecosystem Integration (Phase 11)

**Status:** Phase 11 — stable public API only (no external repository coupling)

The validation framework is **complete**. Phase 11 exposes a stable integration
surface so external AIODOO repositories can consume validation without importing
internal engine modules.

## Dependency direction

```text
Correct:
  aiodoo-training   → aiodoo-validation
  aiodoo-colab      → aiodoo-validation
  aiodoo-models     → aiodoo-validation
  VS Code extension → aiodoo-validation

Incorrect:
  aiodoo-validation → aiodoo-training / aiodoo-colab / aiodoo-models / VS Code
```

```text
External Repository
  ↓
ValidationService (aiodoo_validation.api)
  ↓
ValidationEngine
  ↓
Validation Pipeline
  ↓
ValidationRunResult
  ↓
Consumer formatter (CLI, JSON, HTML, dashboard, etc.)
```

Validation depends on **nobody**. External repositories depend on validation.

After **v1.0.0**, this repository is in **permanent maintenance mode** for
**v1.0.x**. See [MAINTENANCE.md](MAINTENANCE.md).

## Public API

**Stability contract:** Only symbols explicitly exported from ``aiodoo_validation.api``
(and the top-level package where explicitly re-exported via ``__all__``) are
considered the stable public API.

The following modules are **implementation details**. They may change without
notice. External repositories must never import them directly:

- ``aiodoo_validation.engine``
- ``aiodoo_validation.oracles``
- ``aiodoo_validation.scoring``
- ``aiodoo_validation.benchmark``
- ``aiodoo_validation.certification``
- ``aiodoo_validation.reporting``
- ``aiodoo_validation.profiles``
- ``aiodoo_validation.validation_plan``
- ``aiodoo_validation.domain`` (internal types)
- ``aiodoo_validation.ports``
- ``aiodoo_validation.stubs``
- ``aiodoo_validation.inference``
- ``aiodoo_validation.resolution``

Import from ``aiodoo_validation.api`` or the top-level package:

```python
from aiodoo_validation.api import (
    ValidationService,
    build_coding_request,
    get_repository_metadata,
    get_profile_info,
    is_certified,
)
```

| Component | Purpose |
|-----------|---------|
| `ValidationService` | Stable entry point — `validate(request)` |
| `build_coding_request` | Request builder for coding profile |
| `parse_odoo_versions` | Parse comma-separated Odoo versions |
| `get_repository_metadata` | Repository and protocol version metadata |
| `get_profile_info` / `list_profiles` | Profile discovery |
| `capability_labels` | Capability string labels |
| `is_protocol_supported` / `is_profile_supported` / … | Compatibility helpers |
| `is_successful` / `is_certified` / `report_execution` | Result helpers |
| `training_integration_hints` / … | Generic integration hints |

Internal modules (`oracles`, `scoring`, `benchmark`, `certification`, `reporting`,
`engine`) are **not** part of the stable API.

## ValidationService

```python
from aiodoo_validation.api import ValidationService, build_coding_request

service = ValidationService.create_default()
request = build_coding_request(
    base_model_ref="./exports/base",
    adapter_ref="./exports/adapter",
    execution_tier="standard",
)
result = service.validate(request)
```

- `create_default()` — filesystem artifact resolver (production)
- `create_with_stubs()` — stub pipeline (testing)
- `validate(request)` — delegates to `ValidationEngine.run()`

No orchestration changes. No new validation logic.

## Profile discovery

```python
from aiodoo_validation.api import get_profile_info, list_profiles

profiles = list_profiles()  # ("coding",)
profile = get_profile_info("coding")
profile.supported_runtimes
profile.capabilities.supports_reports
profile.pipeline_stages
```

Static metadata only — no filesystem inspection.

## Version and compatibility

```python
from aiodoo_validation.api import get_repository_metadata, is_protocol_supported

metadata = get_repository_metadata()
metadata.repository_version
metadata.protocol.version_label  # "1.0"
metadata.supported_profiles
metadata.supported_execution_tiers
metadata.supported_odoo_versions

is_protocol_supported(1, 0)  # True
is_profile_supported("coding")  # True
```

## Result helpers

```python
from aiodoo_validation.api import is_certified, is_successful, report_execution

if is_successful(result):
    report = report_execution(result)
    certified = is_certified(result)
```

Consumers should use immutable ``ValidationRunResult`` and
``run_context.report_execution`` — never re-run validation for rendering.

## Integration examples

### Training repository

```python
from aiodoo_validation.api import ValidationService, build_coding_request

service = ValidationService.create_default()
request = build_coding_request(
    base_model_ref=export.base_model_path,
    adapter_ref=export.adapter_path,
)
result = service.validate(request)
```

### Colab notebook

```python
from aiodoo_validation.api import ValidationService, build_coding_request

service = ValidationService.create_default()
request = build_coding_request(base_model_ref=base_path, adapter_ref=adapter_path)
result = service.validate(request)
```

### Model repository promotion

```python
from aiodoo_validation.api import summarize_for_promotion

summary = summarize_for_promotion(result)
# Attach summary and result.run_context.report_execution to model record.
```

Generic hint helpers are available:

- `training_integration_hints()`
- `colab_integration_hints()`
- `vscode_integration_hints()`
- `model_repository_integration_hints()`

## CLI integration

The production CLI consumes ``ValidationService`` — no duplicated validation
logic. Terminal formatting remains in ``ConsoleFormatter``.

## Boundary rules

The validation repository must **never** import:

- `aiodoo_training`, `aiodoo_colab`, `aiodoo_models`, `aiodoo_vscode`
- `torch`, `transformers`, `datasets`, `trl`, `peft`, `accelerate`
- `google.colab`, `vscode`, `cursor`

Ecosystem consumers import validation — not the reverse.

## Explicitly not implemented

No training integration, Colab runtime, VS Code extension, model loading, GPU
workloads, dataset generation, HuggingFace coupling, async execution, plugins,
or Phase 12 production hardening.

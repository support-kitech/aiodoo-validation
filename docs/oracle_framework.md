# Oracle Framework (Phase 5)

**Status:** Phase 5 — placeholder oracle execution only (no real validation rules)

The **Oracle Framework** executes the oracle pipeline declared by the
ValidationPlan. The Coding Profile decides *which* oracles run; the Oracle
Framework only *executes* registered implementations.

## Architecture

```text
Validation Engine
    ↓ OracleRunnerPort
OracleEngine
    ↓ OracleRegistry
Placeholder Oracles
    ↓ OracleResult
OracleExecutionResult → RunContext
```

The Validation Engine never contains validation logic. It calls
`OracleRunnerPort.execute_oracles(context)` and attaches the immutable result.

## Components

| Component | Responsibility |
|-----------|----------------|
| `OracleRunnerPort` | Port: execute ValidationPlan oracle pipeline |
| `OracleEngine` | Resolve pipeline stages, run oracles, collect results |
| `OracleRegistry` | Register / lookup oracles by ID (plugin-ready) |
| `Oracle` protocol | Metadata + `execute(OracleContext) → OracleResult` |
| Placeholder oracles | Always-successful stubs (no XML/AST/security scanning) |

## Placeholder oracles (coding)

| ID | Class |
|----|-------|
| `coding.oracle.metadata` | `MetadataOracle` |
| `coding.oracle.manifest` | `ManifestOracle` |
| `coding.oracle.python` | `PythonOracle` |
| `coding.oracle.xml` | `XmlOracle` |
| `coding.oracle.security` | `SecurityOracle` |
| `coding.oracle.module_structure` | `ModuleStructureOracle` |

`coding.oracle.quality` appears in the Coding Profile pipeline as **disabled**
future metadata only — it is not registered and is not executed.

## Lifecycle

1. ValidationPlan attached (Phase 4) with `supports_oracles=True`
2. Inference initialized (Phase 3)
3. `OracleEngine.execute_oracles`:
   - Require `validation_plan` and `validation_profile`
   - Reject capability mismatch
   - For each **enabled** `oracle_pipeline` stage:
     - Resolve oracle from registry
     - Validate supported profile matches plan
     - Execute oracle with `OracleContext`
   - Aggregate into `OracleExecutionResult`
4. Engine attaches `oracle_execution` to `RunContext`

## RunContext integration

After a successful RUN_VALIDATION stage:

- `oracle_execution: OracleExecutionResult`
  - `results: tuple[OracleResult, ...]`
  - `duration_ms`, counts, warnings, errors
  - immutable

## Coding Profile relationship

The Coding Profile owns the oracle pipeline metadata:

```text
Metadata → Manifest → Python → XML → Security → Module Structure
(→ Future Quality disabled)
```

Oracle Framework does not hardcode this order. It reads `ValidationPlan.oracle_pipeline`.

## ValidationPlan relationship

- Enabled stages → executed
- Disabled stages → skipped
- `capabilities.supports_oracles` must be true

## Error handling

Structured `OracleError` / `OracleErrorCode` examples:

- `oracle_not_found` / `unknown_oracle`
- `registration_failure`
- `execution_failure`
- `configuration_failure`
- `profile_mismatch`
- `capability_mismatch`
- `missing_plan` / `missing_profile`

Outcomes are returned to the Validation Engine; the engine never crashes.

## Future extensibility

- Register additional oracles via `OracleRegistry.register`
- Add real validation logic inside oracle `execute` methods in later phases
- Support new profiles by registering profile-scoped oracle IDs
- Quality / scoring oracles remain out of scope until their phases

## Explicitly not implemented (Phase 5)

No XML parsing, AST analysis, Odoo inspection, security scanning, code quality
checks, scoring, benchmarking, certification, reports, or CLI.

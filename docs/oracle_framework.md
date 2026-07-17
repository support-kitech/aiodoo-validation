# Oracle Framework (Phase 5)

**Status:** Phase 5 — placeholder oracle execution only (no real validation rules)

The **Oracle Framework** executes the oracle pipeline declared by the
ValidationPlan. The Coding Profile decides *which* oracles run; the Oracle
Framework only *executes* registered implementations.

## Architecture & dependency direction

```text
domain (OracleResult, OracleExecutionResult, …)
  ↑
ports.OracleRunnerPort
  ↑
oracles (OracleEngine, OracleRegistry, placeholders)
  ↑
engine (orchestration only — no validation logic)

Scoring / Benchmark / Certification MUST NOT be imported by oracles/.
```

```text
Validation Engine
    ↓ OracleRunnerPort
OracleEngine
    ↓ OracleRegistry
Placeholder Oracles
    ↓ OracleResult
OracleExecutionResult → RunContext
    ↓
Scoring Engine (Phase 6 — consumes results only)
```

The Validation Engine never contains validation logic. It calls
`OracleRunnerPort.execute_oracles(context)` and attaches the immutable result.

## Oracle ID convention (frozen)

Format: `{profile}.oracle.{name}`

Centralized in `aiodoo_validation.oracles.ids`. **Do not rename.**

| Constant | ID |
|----------|----|
| `CODING_ORACLE_METADATA` | `coding.oracle.metadata` |
| `CODING_ORACLE_MANIFEST` | `coding.oracle.manifest` |
| `CODING_ORACLE_PYTHON` | `coding.oracle.python` |
| `CODING_ORACLE_XML` | `coding.oracle.xml` |
| `CODING_ORACLE_SECURITY` | `coding.oracle.security` |
| `CODING_ORACLE_MODULE_STRUCTURE` | `coding.oracle.module_structure` |
| `CODING_ORACLE_QUALITY` | `coding.oracle.quality` |

`CODING_ORACLE_QUALITY` is declared in the Coding Profile pipeline as **disabled**
future metadata — it is not registered by default and is not executed.

## Components

| Component | Responsibility |
|-----------|----------------|
| `OracleRunnerPort` | Port: execute ValidationPlan oracle pipeline |
| `OracleEngine` | Resolve pipeline stages, run oracles, collect results |
| `OracleRegistry` | Register / lookup oracles by ID (plugin-ready) |
| `Oracle` protocol | Metadata + `execute(OracleContext) → OracleResult` |
| Placeholder oracles | Always-successful stubs (no XML/AST/security scanning) |

## Placeholder philosophy

Placeholder oracles return successful `OracleResult` values without inspecting
artifacts, parsing XML/Python, scanning security rules, or using inference.
They exist to prove pipeline wiring. Real validation logic is added later
**inside** oracle `execute` methods — never in the Validation Engine or Scoring.

## Lifecycle

1. ValidationPlan attached (Phase 4) with `supports_oracles=True`
2. Inference initialized (Phase 3)
3. `OracleEngine.execute_oracles`:
   - Require `validation_plan` and `validation_profile`
   - Reject capability mismatch
   - For each **enabled** `oracle_pipeline` stage:
     - Resolve oracle from registry by frozen ID
     - Validate supported profile matches plan
     - Execute oracle with `OracleContext`
   - Aggregate into `OracleExecutionResult`
4. Engine attaches `oracle_execution` to `RunContext`

## Registry & future plugins

- Register additional oracles via `OracleRegistry.register`
- Resolve by frozen oracle ID
- Support new profiles with `{profile}.oracle.{name}` IDs
- No hardcoded branching in Validation Engine

## RunContext integration

After a successful RUN_VALIDATION stage:

- `oracle_execution: OracleExecutionResult`
  - `results: tuple[OracleResult, …]`
  - `duration_ms`, counts, warnings, errors
  - immutable

## Coding Profile relationship

The Coding Profile owns the oracle pipeline metadata (IDs from `oracles.ids`):

```text
Metadata → Manifest → Python → XML → Security → Module Structure
(→ Future Quality disabled)
```

Oracle Framework does not hardcode this order. It reads `ValidationPlan.oracle_pipeline`.

## Explicitly not implemented in the Oracle Framework

No scoring, benchmarking, certification, reports, CLI, XML parsing, AST analysis,
Odoo inspection, security scanning, or code quality checks.

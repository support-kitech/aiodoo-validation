# Oracle Framework

**Status:** Production structural oracles active; behavioral oracle architecture ready

The **Oracle Framework** executes the oracle pipeline declared by the
ValidationPlan. Profiles decide *which* oracles run; the Oracle Framework only
*executes* registered implementations.

## Architecture & dependency direction

```text
domain (OracleResult, OracleExecutionResult, …)
  ↑
ports.OracleRunnerPort
  ↑
oracles (OracleEngine, OracleRegistry, structural, behavioral architecture)
  ↑
engine (orchestration only — no validation logic)

Scoring / Benchmark / Certification MUST NOT be imported by oracles/.
behavior/ and comparators/ may be used by behavioral oracles only.
```

## Validation kinds

| Kind | Module | Production |
|------|--------|------------|
| Structural | `oracles.structural` | Registered for all adapter profiles |
| Behavioral | `oracles.behavioral` | Architecture only until corpora exist |

See [behavioral_validation.md](behavioral_validation.md).

## Oracle ID convention (frozen)

Format: `{profile}.oracle.{name}`

Behavioral future IDs: `{profile}.oracle.behavior.{name}`

Centralized coding IDs remain in `aiodoo_validation.oracles.ids`. **Do not rename.**

| Constant | ID |
|----------|----|
| `CODING_ORACLE_METADATA` | `coding.oracle.metadata` |
| `CODING_ORACLE_MANIFEST` | `coding.oracle.manifest` |
| `CODING_ORACLE_PYTHON` | `coding.oracle.python` |
| `CODING_ORACLE_XML` | `coding.oracle.xml` |
| `CODING_ORACLE_SECURITY` | `coding.oracle.security` |
| `CODING_ORACLE_MODULE_STRUCTURE` | `coding.oracle.module_structure` |
| `CODING_ORACLE_QUALITY` | `coding.oracle.quality` |

`CODING_ORACLE_QUALITY` remains declared as **disabled** future metadata.

## Soft evaluation failures

Oracle evaluation failures (`success=False` without hard `OracleError`s) are
recorded and continue the pipeline so scoring/certification can deny
certification instead of aborting as `FAILED`.

## Components

| Component | Responsibility |
|-----------|----------------|
| `OracleRunnerPort` | Port: execute ValidationPlan oracle pipeline |
| `OracleEngine` | Resolve pipeline stages, run oracles, collect results |
| `OracleRegistry` | Register / lookup oracles by ID |
| `Oracle` protocol | Metadata + `execute(OracleContext) → OracleResult` |
| Structural oracles | Artifact contract checks |
| Behavioral oracles | Prompt → inference → comparator (deferred without corpus) |
| Placeholder oracles | Stub path / unit tests only |

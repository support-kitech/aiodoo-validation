# Report Generation (Phase 9)

**Status:** Phase 9 — placeholder report objects only (no rendering or export)

The **Report Generator** consumes `CertificationExecutionResult` and produces
immutable report objects. It never inspects XML, Python, manifests, security
files, or the filesystem. It never re-runs validation, scoring, benchmarking,
or certification.

## Architecture & dependency rule

```text
Correct:
  CertificationExecutionResult → ReportGenerator → ReportExecutionResult

Incorrect:
  ReportGenerator → Oracle / Score / Benchmark / XML / Python / filesystem
```

```text
Validation Engine
    ↓ CertificationEnginePort
Certification Engine
    ↓ certification_execution on RunContext
ReportGeneratorPort
    ↓ ReportGenerator → ReportRegistry → ReportTemplate
ReportExecutionResult → RunContext.report_execution
```

## Components

| Component | Responsibility |
|-----------|----------------|
| `ReportGeneratorPort` | Port: `generate_report(context) → ReportExecutionOutcome` |
| `ReportGenerator` | Read plan/profile/certification results; run templates |
| `ReportRegistry` | Register / resolve templates by ID (plugin-ready) |
| `ReportTemplate` protocol | Metadata + `generate(ReportContext) → ReportResult` |
| Placeholder templates | Deterministic `status=SUCCESS`, `summary=Placeholder report` |

## Report ID convention (frozen)

Format: `{profile}.report.{name}` — maps 1:1 to `{profile}.certification.{name}`

Centralized in `aiodoo_validation.reporting.ids`.

**These IDs are frozen and must never be renamed.** Future phases and plugins
must reuse them unchanged.

| Template ID | Source Certification Policy ID |
|-------------|--------------------------------|
| `coding.report.metadata` | `coding.certification.metadata` |
| `coding.report.manifest` | `coding.certification.manifest` |
| `coding.report.python` | `coding.certification.python` |
| `coding.report.xml` | `coding.certification.xml` |
| `coding.report.security` | `coding.certification.security` |
| `coding.report.module_structure` | `coding.certification.module_structure` |
| `coding.report.quality` | `coding.certification.quality` (disabled in plan) |

## What Report Generation does NOT do

Report generation **never**:

- validates artifacts or runs oracles
- scores findings or benchmarks scores
- certifies benchmark results (certification already happened upstream)
- parses XML / Python / manifests
- inspects the filesystem
- executes inference
- renders PDF, HTML, Markdown, or JSON export

Report generation **only** consumes `CertificationExecutionResult` /
`CertificationResult` and produces structured protocol objects.

## Lifecycle

1. Require `validation_plan`, `validation_profile`, `certification_execution`
2. Require `capabilities.supports_reports`
3. For each **enabled** `report_pipeline` stage:
   - Resolve template from registry
   - Match profile
   - Locate matching `CertificationResult` by `source_certification_policy_id`
   - Invoke template with `ReportContext` (certification result only)
4. Aggregate into `ReportExecutionResult` with `ReportResult[]`
5. Attach to `RunContext.report_execution`

## Placeholder behavior

Each enabled template returns:

- `status = SUCCESS`
- `summary = Placeholder report`
- One summary section per report
- No markdown, PDF, HTML, JSON export, or formatting

**`overall_status`, placeholder summaries, and placeholder sections are NOT
production report output.** The placeholder report objects exist only to validate
the Report Generator pipeline. Future rendering integrations (CLI formatting,
Markdown, HTML, PDF, JSON, dashboards, API responses, etc.) will consume these
immutable report objects. These placeholder values must never be interpreted as
production report rendering.

Rendering belongs to future integrations (CLI, dashboards, ecosystem tools).

## RunContext integration

After successful REPORT:

- `report_execution: ReportExecutionResult`

Full context after Phase 9:

`artifact_bundle` · `validation_profile` · `validation_plan` · `inference_session`
· `oracle_execution` · `score_execution` · `benchmark_execution`
· `certification_execution` · `report_execution`

## Error handling

Structured `ReportError` / `ReportErrorCode`:

- `missing_certification_results` / `missing_plan` / `missing_profile`
- `template_not_found` / `registration_failure`
- `capability_mismatch` / `profile_mismatch`
- `certification_result_missing` / `execution_failure` / `configuration_failure`

## Future extensibility

- Register real report templates inside template `generate` methods
- Enable quality report when quality certification is enabled
- New profiles: `{profile}.report.{name}` consuming matching certification IDs
- External renderers consume `ReportExecutionResult` without changing the engine

## Explicitly not implemented

No PDF/HTML/Markdown/JSON export, UI, protocol serialization, validation,
scoring, benchmarking, certification, filesystem inspection, or ecosystem
integrations beyond the production CLI terminal formatter.

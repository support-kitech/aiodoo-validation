# Report Generation

**Status:** Production machine-readable report objects; no file export/rendering

The **Report Generator** consumes `CertificationExecutionResult` (and a
`run_summary` snapshot from `RunContext`) to produce immutable report objects.
It never re-runs validation, scoring, benchmarking, or certification, and does
not parse artifacts from disk.

Production templates include sections for execution tier, profile, structural
validation, behavior validation status, scores, benchmark, certification
decision/reasons, timing, artifacts, and warnings. Behavior sections report
`deferred` (`BehaviorStatus.DEFERRED`) until behavioral oracles are enabled.

## Architecture & dependency rule

```text
Correct:
  CertificationExecutionResult (+ run_summary) → ReportGenerator → ReportExecutionResult

Incorrect:
  ReportGenerator → re-run Oracle / Score / Benchmark / filesystem parsing
```

## Production vs stub

| Path | Behavior |
|------|----------|
| Filesystem / CLI default | Rich production sections + `machine_readable` metadata |
| Stub path | Placeholder `"Placeholder report"` summaries for wiring tests |

CLI formatting reads `report_execution` for terminal display. PDF/HTML/Markdown
export remains a consumer integration concern.

## Explicitly deferred

- PDF / HTML / Markdown / JSON file export
- Dashboard UIs
- Behavior detail sections until corpora exist

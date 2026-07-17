# Production CLI (Phase 10)

**Status:** Phase 10 — human-readable terminal output only

The **CLI** presents completed validation runs to users. It accepts input,
calls ``ValidationService``, and formats ``ValidationRunResult`` for the
terminal. It never validates, scores, benchmarks, certifies, generates reports,
parses artifacts, or inspects the filesystem directly.

## Architecture & dependency rule

```text
Correct:
  User → CLI → ValidationService → ValidationRunResult → ConsoleFormatter → Terminal

Incorrect:
  CLI → Oracle / Scoring / Benchmark / Certification / ReportGenerator / Filesystem
```

```text
User
  ↓
CLI (validate | version | capabilities | help)
  ↓
ValidationService.validate(ValidationRequest)
  ↓
ValidationRunResult / RunContext.report_execution
  ↓
ConsoleFormatter
  ↓
stdout
```

## Commands

| Command | Description |
|---------|-------------|
| `validate` | Run the Validation Protocol V1 lifecycle |
| `version` | Show repository and protocol metadata |
| `capabilities` | Show supported profiles, stages, and capabilities |
| `help` | Show usage and examples |

## Validate

```bash
aiodoo-validation validate \
    --profile coding \
    --base-model ./base \
    --adapter ./adapter
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--profile` | No | `coding` | Validation profile name |
| `--base-model` | Yes | — | Base model artifact path or reference |
| `--adapter` | Yes | — | Adapter artifact path or reference |
| `--merged-model` | No | — | Optional merged model reference |
| `--execution-tier` | No | `standard` | `smoke`, `standard`, or `full` |
| `--run-id` | No | generated | Optional run identifier |
| `--odoo-versions` | No | `17,18,19` | Comma-separated Odoo major versions |
| `--debug` | No | off | Show tracebacks for unexpected errors |

The CLI builds a ``ValidationRequest``, invokes ``ValidationService.create_default().validate()``,
and prints:

- overall exit status
- pipeline stage summary
- warnings and errors
- report summary from ``RunContext.report_execution``

## Version

```bash
aiodoo-validation version
```

Displays repository version, protocol version, supported profiles, and execution
tiers from static metadata.

## Capabilities

```bash
aiodoo-validation capabilities
```

Displays supported profiles, pipeline stages, profile capabilities, runtimes, and
artifact types from static coding profile metadata. No filesystem inspection.

## Help

```bash
aiodoo-validation help
python3 -m aiodoo_validation
```

Running the module without a subcommand also shows help.

## Entry points

Both invoke the same CLI application:

```bash
python3 -m aiodoo_validation validate --base-model ./base --adapter ./adapter
./scripts/aiodoo-validation validate --base-model ./base --adapter ./adapter
```

After editable install, the ``console_scripts`` entry point is also available:

```bash
pip install -e .
aiodoo-validation version
```

## Exit codes

| Exit status | Code |
|-------------|------|
| `completed` (certified) | `0` |
| `not_certified` | `1` |
| `failed` / `internal_error` | `2` |
| `invalid_request` | `3` |

## Console formatter

``ConsoleFormatter`` is intentionally **presentation-only**. It consumes immutable
``ValidationRunResult`` objects and converts them into human-readable terminal
output.

Future integrations (JSON, HTML, PDF, API, VS Code, dashboards, Web UI) must
consume immutable report objects rather than re-running validation.

``ConsoleFormatter`` produces plain text output:

- run metadata and duration
- pipeline stage statuses
- warnings and errors
- report template summary

No Markdown, HTML, PDF, JSON, colors, progress bars, or interactive UI.

## Error handling

- Invalid arguments → friendly message, exit code `3`
- Pipeline failures → formatted result output, mapped exit code
- Unexpected exceptions → friendly message unless `--debug` or
  `AIODOO_VALIDATION_DEBUG=1` is set

## What the CLI does NOT do

No validation logic, scoring, benchmarking, certification, report generation,
filesystem artifact parsing, JSON/HTML/Markdown/PDF export, API server, dashboard,
TUI, async execution, or direct ecosystem repository imports.

## Configuration

- ``CliConfig`` — program name and debug flag
- ``AIODOO_VALIDATION_DEBUG`` environment variable enables tracebacks

No repository configuration redesign.

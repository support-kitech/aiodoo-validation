# Contract Adoption (Phase 4)

Scope: how `aiodoo-validation` consumes `aiodoo_contract` (the canonical
Capability Contract package — see `ecosystem-v2-certification/
ARCHITECTURE_FREEZE_REPORT.md` and the ADRs in `aiodoo-contract/docs/adr/`).

`aiodoo-validation` is the **third** canonical consumer of `aiodoo_contract`,
after `aiodoo-datasets` (`aiodoo-datasets/CONTRACT_ADOPTION.md`) and
`aiodoo-training` (`aiodoo-training/CONTRACT_ADOPTION.md`). This document
records what was adopted, how, and why, and — per the ADR-0005/ADR-0007
ownership rules ("everything shared lives in exactly one place") — every case
where this repository still defines something of its own, with the reason it
is not a duplicate contract.

Validation's frozen architecture (structural validation, behavioral
validation, benchmark execution, certification, report generation, scoring)
is unchanged. Everything below is a **surgical, additive** integration on top
of it — no frozen port signature changed.

## 1. What "adoption" means here

`aiodoo-validation` does not import `aiodoo-datasets` or `aiodoo-training` as
Python dependencies (there is no validation → datasets / validation →
training dependency edge — see `docs/adr/0008-dependency-graph.md` in
`aiodoo-contract`). It consumes native fixtures and `aiodoo-datasets`
evaluation corpora purely as on-disk JSONL, normalized by each capability's
`CapabilityRecordParser` (`aiodoo_validation/capabilities/*/parser.py`) into
`ParsedCapabilityRecord` — validation's own, pre-existing, capability-agnostic
domain type (`aiodoo_validation/domain/capability_record.py`). That normalized
record is the boundary validation controls, so it re-implements the same
narrow projection step aiodoo-training performs on its own (richer) record
shape — against the one canonical target (`aiodoo_contract.schemas`), never
redefining the target itself.

### `aiodoo_validation/contract/` — the adapter/bridge package

New package, validation's consumer-side equivalent of aiodoo-training's
`aiodoo_training/contract/` and aiodoo-datasets' `generators/common/contract/`:

- **`adapters.py`** — `project_<capability>(record) -> ContractProjection`
  for every capability with a canonical shape (`coding`, `planner`, `repair`,
  `execution`, `conversation`, `approval`), mapping validation's own
  `ParsedCapabilityRecord` onto the exact
  `aiodoo_contract.schemas.<capability>` Pydantic request/response models.
  `project_record()` dispatches by `record.capability_id`. Malformed/
  under-specified input raises `ContractAdapterError` (never a bare
  `KeyError`/`TypeError`/`pydantic.ValidationError`), so callers can treat
  "this record does not carry enough structure to project" as a distinct,
  expected, fail-closed outcome.
- **`prompt_bridge.py`** — the *only* place in this repository that turns a
  capability request into prompt text. `render_capability_prompt()`
  delegates every formatting decision to
  `aiodoo_contract.prompts.CapabilityPromptBuilder`; `render_chat_prompt()`
  delegates every chat-turn rendering decision to
  `aiodoo_contract.templates.get_chat_template(...).render_validation()` (the
  ADR-reserved certification-inference entry point, guaranteed identical to
  `render_runtime()`); `render_inference_prompt()` composes the two into the
  single end-to-end call the behavior pipeline uses.
- **`parser_bridge.py`** — the *only* place in this repository that
  interprets model-generated text for a contract-mapped capability.
  `parse_capability_output()` decodes raw text via
  `aiodoo_contract.parsers.CapabilityParser` and then validates the result
  via `aiodoo_contract.validators.ContractValidator` — the exact parser/
  validator pair `aiodoo-core`'s runtime agent loop will use on the same
  model's output. Deliberately fail-closed: raises `ContractParseError`
  (never a partial/best-effort result) on any decode or validation failure.
  `extract_comparable_text()` reduces a canonical response back to the plain
  text validation's pre-existing comparators operate on, so contract
  adoption did not require rewriting any comparator.
- **`version_check.py`** — `VALIDATION_CONTRACT_VERSION` (the pinned contract
  version this integration was built and tested against) and
  `ensure_contract_compatible()`, which wraps
  `aiodoo_contract.version.check_compatibility`. Called at the top of
  `CertificationEngine._certify()` (Section 5) — never invented locally.

## 2. Prompt Builder

**Removed:** nothing pre-existing — behavioral inference previously sent
`case.prompt.text`, the record's raw `problem` string, with no formatting
step of its own to remove. There was no local prompt-builder class to
delete; the gap was the *absence* of contract-aligned prompt construction,
not a competing implementation of it.

**Added:** `CapabilityBehaviorPipeline._contract_projection_metadata()`
(`aiodoo_validation/behavior/capability_pipeline.py`) projects each parsed
record via `aiodoo_validation.contract.adapters.project_record` and renders
its prompt via `aiodoo_validation.contract.prompt_bridge.render_inference_prompt`
— which calls `aiodoo_contract.prompts.CapabilityPromptBuilder` exclusively.
The rendered text is attached to `BehaviorCase.metadata["contract_prompt_text"]`
(never mutating `BehaviorCase.prompt`, which `BehaviorCaseBuilder` and its
existing tests still own — Section 6), and `BehaviorRunner.run_case()` sends
it to the inference runner instead of the raw `problem` string whenever the
case is contract-mapped.

**Observable effect:** every contract-mapped case's behavioral inference call
now carries the capability's default system prompt and instruction framing
from `CapabilityPromptBuilder`, byte-for-byte identical to what
`aiodoo-training`'s `prompt_bridge.build_training_example()` teaches for the
same contract request. Integration test fixtures
(`tests/integration/test_*_behavior_pipeline.py`,
`test_e5_production_behavior_wiring.py`) were updated: their scripted
inference runners now match on a *substring* of the rendered prompt (the
original instruction text still appears verbatim inside it — see
`aiodoo_contract.prompts.builder.PromptBuilder`) rather than an exact match
against the bare `problem` string.

## 3. Chat Template

**Removed:** nothing pre-existing, for the same reason as Section 2 —
behavioral inference had no local chat-turn formatting to remove.

**Added:** `prompt_bridge.render_chat_prompt()` is the sole call site that
turns a `RenderedPrompt` (system + user text) into model-ready text, via
`aiodoo_contract.templates.get_chat_template(name).render_validation(...)`.
`DEFAULT_CHAT_TEMPLATE_NAME = "generic"` — a plain-text, role-prefixed
rendering with no special tokens, safe for the stub/scripted runners used in
tests and any real runtime. `CapabilityBehaviorPipeline.chat_template_name`
is a constructor field, so a caller can select `"qwen"`/`"deepseek"`/any
other name `aiodoo_contract.templates.registry` exposes without validation
inventing its own template-selection mechanism.

Training and validation now render prompts through the identical
`aiodoo_contract.prompts.CapabilityPromptBuilder` → `aiodoo_contract.templates`
pipeline for the same contract request — the single remaining
training/validation prompt-format mismatch the architecture audits flagged
is closed.

## 4. Schemas

Every contract-mapped capability's request/response shape is exclusively
`aiodoo_contract.schemas.<capability>.*`:

| Capability | Request | Response |
| :--- | :--- | :--- |
| Coding | `CodingRequest` | `CodingResponse` (`FileEdit`) |
| Planner | `PlannerRequest` | `PlannerResponse` (`PlanStep`) |
| Repair | `RepairRequest` | `RepairResponse` (`RepairFix`) |
| Execution | `ExecutionRequest` | `ExecutionResponse` |
| Conversation | `ConversationRequest` | `ConversationResponse` (`ConversationTurn`) |
| Approval | `ApprovalRequest` | `ApprovalResponse` |

Validation defines no `Request`/`Response` model of its own for any of these
six capabilities. `ParsedCapabilityRecord`/`CapabilityArtifact` (Section 6)
remain validation's own, pre-existing, capability-agnostic *input*
representation — the adapter layer's job is exclusively to project that onto
the schemas above, not to redefine them.

## 5. Parsers, Validators & Versioning

**Parsers:** `BehaviorRunner.run_case()`
(`aiodoo_validation/behavior/__init__.py`) calls
`aiodoo_validation.contract.parser_bridge.parse_capability_output()` for
every contract-mapped case, which decodes the model's raw generated text via
`aiodoo_contract.parsers.CapabilityParser` — the same decoder
`aiodoo-core`'s runtime will use. Validation owns no parser of model output
for any of the six contract-mapped capabilities.

**Validators:** the same `parse_capability_output()` call also runs the
decoded response through `aiodoo_contract.validators.ContractValidator`
before it is ever compared against `ExpectedOutput`. A response that decodes
but fails contract validation (or fails to decode at all) is recorded as a
`contract_parse_failed` finding and the case fails — never silently compared
as raw text (Section 7).

**Versioning:** `CertificationEngine._certify()`
(`aiodoo_validation/certification/engine.py`) calls
`aiodoo_validation.contract.version_check.ensure_contract_compatible()` as
its first action — before checking for a plan, profile, or benchmark
results. An incompatible installed contract raises `ContractVersionError`,
which `_certify()` turns into a `CertificationExecutionOutcome(success=False)`
carrying a new `CertificationErrorCode.CONTRACT_VERSION_INCOMPATIBLE` error
(`field="contract_version"`) — certification never runs against schemas,
prompts, parsers, or validators the installed contract does not actually
provide. This is validation's fail-early gate, the mirror of
`aiodoo-training`'s `ensure_contract_compatible()` call at the top of
`run_train_from_config()`.

## 6. Certification artifacts — contract & capability metadata

`CertificationExecutionResult.metadata` (populated in
`CertificationEngine._certify()`) now always includes:

- **`contract_version`** — `aiodoo_validation.contract.version_check.VALIDATION_CONTRACT_VERSION`,
  the contract version this certification run's behavioral validation was
  executed against (not the installed contract's own version — the pinned
  consumer version certification just proved compatible with, per Section 5).
- **`capability`** — `plan.profile_name`, the capability this certification
  run certified.

This is purely additive to the existing `registry_pipeline` metadata key and
every existing `CertificationExecutionResult`/`CertificationResult` field
(`policy_id`, `certified`, `certification_score`, `certification_level`,
`errors`, `warnings`, …) — no certification artifact field was renamed or
removed. `ReportContext.certification_execution` already carries the full
`CertificationExecutionResult`, so report templates have access to
`contract_version`/`capability` through the existing certification-consuming
port without any change to `ReportContext`, `ReportResult`, or the report
generation pipeline.

## 7. Behavioral validation reliability

| Behavior | Before | After |
| :--- | :--- | :--- |
| Contract projection fails (e.g. `evaluation`, or a native fixture missing required artifacts) | N/A — no projection existed | Recorded as `contract_mapped=False` with `contract_projection_error` in case metadata; the case falls back to its legacy raw-`problem` prompt/comparison path. A documented, **observable** fallback (inspectable in `BehaviorCase.metadata`), not a silent one — see the docstring on `CapabilityBehaviorPipeline._contract_projection_metadata`. |
| Prompt rendering raises for a contract-mapped case | N/A | Caught and recorded the same way (`contract_mapped=False`, `contract_projection_error`) — corpus assembly (`CapabilityBehaviorPipeline.assemble`) never crashes because one record's prompt failed to render. |
| Model output for a contract-mapped case does not decode, or decodes but fails `ContractValidator` | N/A — no contract-aware parsing existed | `BehaviorRunner.run_case()` returns `BehaviorResult(passed=False, findings=("contract_parse_failed",), metadata={"contract_response_valid": False, "contract_error": ...})` — an explicit behavioral failure, never a silent fallback to comparing the malformed raw text. |
| Comparing contract-decoded text against un-normalized expected text | N/A | `aiodoo_contract`'s `ContractModel` sets `str_strip_whitespace=True` (ADR-0007) on every string field, so any text that round-trips through a contract response has its surrounding whitespace normalized by construction. `BehaviorRunner.run_case()` strips `ExpectedOutput.text` identically before comparison for contract-mapped cases only, so an EXACT comparator cannot spuriously fail on whitespace alone — `BehaviorResult.expected` still reports the original, un-normalized gold text for traceability. |

Existing engine-level reliability guarantees audited and confirmed already
in place, unchanged by this phase: every top-level `*Engine.{verb}()`
(`BehaviorRunner`, `CertificationEngine`, `ReportGenerator`,
`BenchmarkEngine`, `ScoringEngine`, `OracleEngine`, `ProfileEngine`,
`InferenceRunner`) catches unexpected exceptions at its boundary and returns
a structured, `success=False` result carrying the original error — never a
bare `pass`/swallowed exception. This phase's contract-integration failure
modes (this section, plus Sections 5–6) were layered on top of that
pre-existing pattern, not a replacement for it.

## 8. Duplication that was **not** removed, and why

Per the primary goal ("if duplication cannot be removed, document the
reason"), the following were audited against `aiodoo_contract` and
deliberately **not** replaced with imports:

- **`domain/capability_record.py::ParsedCapabilityRecord`/`CapabilityArtifact`/`TransformationDescriptor`**
  vs. `aiodoo_contract.schemas.*` — this is validation's frozen (pre-Phase-4),
  capability-agnostic parse of raw corpus JSON, produced by every
  `CapabilityRecordParser` before `BehaviorCaseBuilder` ever runs. It exists
  precisely because corpus records can be malformed, artifact-only, or
  otherwise not yet representable in any contract shape — `ParsedCapabilityRecord`
  has to accept those and let the *adapter* (Section 1) be the point that
  either projects successfully or raises `ContractAdapterError`. Collapsing
  it into `aiodoo_contract.schemas` would require every corpus record to
  already be contract-conformant before validation could even parse it,
  eliminating the "this record wasn't contract-representable" diagnostic
  this phase added (Section 7). Not a strict duplicate either: it carries no
  capability-specific fields (no `instruction`, `goal`, `fix`) — those are
  precisely what the per-capability projector functions in `adapters.py`
  synthesize.
- **`capabilities/*/parser.py` (`CodingRecordParser`, `PlannerRecordParser`,
  etc.)** vs. `aiodoo_contract.parsers` — these parse *raw corpus JSON* (a
  file-format concern: native task shape, training-JSONL envelope, or
  compact fixture shape) into `ParsedCapabilityRecord`. `aiodoo_contract.parsers`
  parses *model-generated text* into a `CapabilityResponse` — the opposite
  direction and a different input entirely. There is no overlap to remove:
  behavioral validation now uses both, in the right place — corpus parsers
  before the adapter projects, `aiodoo_contract.parsers` (via
  `parser_bridge.py`) after the model generates.
- **`domain/request.py::ValidationRequest`** vs.
  `aiodoo_contract.schemas.base.CapabilityRequest` — `ValidationRequest` is
  the top-level *Validation Protocol* request (which model/adapter to
  certify, which profile, execution tier, Odoo versions, fingerprint policy)
  — an orchestration input to the whole validation run, not a capability
  request/response pair. `aiodoo_contract` has no equivalent concept.
- **`domain/inference.py` (`GenerationRequest`, `GenerationMetadata`,
  `InferenceResult`, `InferenceSession`, …)** — inference-runtime plumbing
  (prompt string + sampling parameters in, token counts + latency +
  generated text out) that predates and is orthogonal to the contract's
  request/response schemas. `GenerationRequest.prompt` is exactly where the
  contract-rendered prompt text (Section 2) is threaded through — there is
  nothing here that competes with a contract schema.
- **`domain/report.py`, `reporting/templates.py`, `reporting/engine.py`** —
  certification *report* generation (Markdown/JSON sections, warnings,
  scores) is validation-owned, audit-scoped output, not a capability
  request/response or a chat-template rendering concern. `templates.py`'s
  name is a coincidence of vocabulary — it renders report sections, not chat
  turns; `aiodoo_contract.templates` renders chat turns, not reports. No
  overlap.
- **`evaluation` capability has no contract projection** — same documented
  gap `aiodoo-datasets` and `aiodoo-training` record in their own adapter
  modules: `aiodoo_contract.schemas.evaluation.EvaluationRequest`/`Response`
  model a single verdict on *another* capability's candidate output vs. an
  expectation; `ParsedCapabilityRecord` (a single problem/artifact record)
  does not carry the candidate+expectation+rubric structure needed to
  reconstruct one. `is_contract_mapped_capability("evaluation")` returns
  `False`; its behavioral cases use the pre-Phase-4 raw-text prompt and
  comparison path, unchanged.
- **Planner/Repair/Approval/Conversation single-step simplifications** —
  `project_planner` synthesizes exactly one `PlanStep` (there is no native
  multi-step plan representation in `ParsedCapabilityRecord`); `project_approval`
  always projects `ApprovalStatus.APPROVED` (there is no native
  decision/verdict field — validation's approval corpora express the outcome
  as free-text `explanation`). Both are documented, intentional
  simplifications in the adapter docstrings, not a claim that the source
  corpora only ever have one step or one outcome — they are what the current
  fixture shapes actually carry.

## 9. Backward compatibility

- The frozen `InferenceRunnerPort`, `BehaviorCaseBuilder`,
  `ComparatorRegistry`/`Comparator`, `CertificationPolicy`, `ReportGenerator`
  ports and every existing capability pack registration are unchanged. Every
  existing call site works unmodified for non-contract-mapped cases
  (`evaluation`) and for any case where contract projection is unavailable.
- **Intentional, observable change:** contract-mapped capabilities'
  behavioral inference calls now receive the full chat-templated contract
  prompt instead of the bare `problem` string (Section 2) — any external
  tooling asserting an exact prompt string for
  `coding`/`planner`/`repair`/`execution`/`conversation`/`approval` behavior
  cases needs to expect the templated form. `evaluation` is unchanged (still
  the raw `problem` string).
- **Intentional, observable change:** a contract-mapped case whose model
  output fails to decode/validate against `aiodoo_contract` now fails with
  `findings=("contract_parse_failed",)` instead of being compared as raw
  text (Section 7) — this can turn a previously-passing (accidentally,
  against malformed output) case into a failure. This is the audit-mandated
  "runtime and validation must interpret model output identically" fix, not
  a regression: a response `aiodoo-core`'s runtime would also reject is now
  rejected here too.
- `CertificationExecutionResult.metadata`'s new `contract_version`/
  `capability` keys (Section 6) are additive; no existing metadata key was
  renamed or removed.
- A certification run against an incompatible installed `aiodoo_contract`
  now fails immediately with `CONTRACT_VERSION_INCOMPATIBLE` (Section 5)
  instead of proceeding and potentially certifying against schemas/prompts
  the installed contract does not provide — an intentional, audit-mandated
  fail-closed change.

## 10. Deferred / out of scope for this phase

- **Contract projection for `evaluation`** — closing this gap requires either
  a richer `ParsedCapabilityRecord` (an architectural change to a frozen
  domain type, out of scope) or a new `aiodoo_contract.schemas.evaluation`
  shape (out of scope — `aiodoo-contract` is frozen for this phase). Tracked
  as the same open gap `aiodoo-datasets`/`aiodoo-training` already document.
- **Multi-step `PlannerResponse` / structured `ApprovalResponse` verdicts
  from richer fixtures** — the single-`PlanStep`/always-`APPROVED`
  simplifications in Section 8 are correct for what `ParsedCapabilityRecord`
  currently carries; extending the corpus fixture format (or
  `ParsedCapabilityRecord` itself) to carry multi-step plans or real
  approval verdicts is a fixture/domain-model change, not a contract-adoption
  change, and out of scope here.
- Broadening `ContractComplianceRule`-equivalent structural pre-flight
  checking (the `WARNING`-severity pattern `aiodoo-datasets` uses) into
  validation's own corpus-loading path — validation's contract compliance is
  currently enforced per-case, at behavioral-inference time
  (`contract_parse_failed`), not as a separate corpus-wide pre-flight pass.
  Adding one is additive future work, not required to meet this phase's
  success criteria.
- Any change to `aiodoo-contract`, `aiodoo-datasets`, `aiodoo-training`,
  `aiodoo-model`, `aiodoo-core`, `aiodoo-vscode`, `aiodoo-colab` — out of
  scope per this phase's instructions.

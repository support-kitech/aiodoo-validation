# Inference Runner (Phase 3)

**Status:** Phase 3 — loading and generation only (no validation logic)

The **Inference Runner** loads validated artifacts from the immutable
`ArtifactBundle`, attaches the coding adapter, and exposes a generation
interface. All model-specific code stays behind `ModelRuntimePort`.

## Architecture

```text
Validation Engine
    ↓ InferenceRunnerPort
Inference Runner (Real / Stub)
    ↓ ModelRuntimePort
Model Runtime (Mock / Qwen HF)
    ↓
Loaded Model Handle (opaque)
```

No layer above the inference runner may import Torch, Transformers, PEFT,
or Qwen-specific code.

## Supported scope

| Component | Phase 3 support |
|-----------|-----------------|
| Base model | Qwen3-8B (`model_family=qwen`, `identifier=qwen3-8b`) |
| Adapter | AIODOO coding adapter (`adapter_type=coding`) |
| Rejected | planner, repair, conversation, execution adapters |

## Lifecycle

1. **Initialize** — validate bundle compatibility and load paths
2. **Load base model** — via model runtime
3. **Attach adapter** — PEFT attach in Qwen runtime (mock skips)
4. **Verify load** — runtime health check
5. **Ready** — `InferenceSession` attached to `RunContext`
6. **Shutdown** — unload and release resources on pipeline exit

## Generation interface

```python
GenerationRequest(
    prompt="...",
    max_tokens=256,
    temperature=0.7,
    seed=42,  # optional
)
```

`InferenceResult` returns:

- `generated_text`
- `prompt_tokens`, `completion_tokens`, `total_tokens`
- `latency_ms`
- `memory_usage_mb` (placeholder in mock runtime)
- `metadata` (`GenerationMetadata`)

No scoring or validation is performed on generated text in Phase 3.

## Implementations

| Runner | Runtime | Use case |
|--------|---------|----------|
| `StubInferenceRunner` | `MockModelRuntime` | Default CI / `ValidationEngine.with_stubs()` |
| `RealInferenceRunner` | `MockModelRuntime` | `ValidationEngine.with_mock_inference()` |
| `RealInferenceRunner` | `QwenModelRuntime` | Optional local inference (`requirements/inference.txt`) |

## Artifact load paths

Filesystem artifact resolution stores inference-only paths in bundle metadata
under `_artifact_paths`. Inference never reads `ValidationRequest` paths.

## Error handling

Structured `InferenceError` codes include:

- `missing_bundle`, `unsupported_model`, `unsupported_adapter`
- `model_load_failure`, `adapter_load_failure`, `oom`
- `unsupported_config`, `generation_failure`, `not_initialized`

Failures during `initialize_inference` set exit status `failed` and skip
downstream stages without crashing the engine.

## Fingerprint / memory notes

- Mock runtime reports a fixed `memory_usage_mb` placeholder.
- Qwen runtime leaves `memory_usage_mb` as `None` until resource telemetry
  is added in a later phase.

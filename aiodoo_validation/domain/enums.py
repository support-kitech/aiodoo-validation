"""Domain enumerations for aiodoo-validation."""

from enum import IntEnum, StrEnum


class ExecutionTier(StrEnum):
    """Validation execution tier (behavior unchanged in Phase 0/1)."""

    SMOKE = "smoke"
    STANDARD = "standard"
    FULL = "full"


class ExitStatus(StrEnum):
    """Structured pipeline exit status."""

    COMPLETED = "completed"
    NOT_CERTIFIED = "not_certified"
    FAILED = "failed"
    INVALID_REQUEST = "invalid_request"
    INTERNAL_ERROR = "internal_error"


class ValidationStage(StrEnum):
    """Ordered validation pipeline stages."""

    LOAD_REQUEST = "load_request"
    VALIDATE_REQUEST = "validate_request"
    RESOLVE_ARTIFACTS = "resolve_artifacts"
    RESOLVE_PROFILE = "resolve_profile"
    INITIALIZE_INFERENCE = "initialize_inference"
    RUN_VALIDATION = "run_validation"
    SCORING = "scoring"
    BENCHMARK = "benchmark"
    CERTIFICATION = "certification"
    REPORT = "report"
    EXIT = "exit"


class StageStatus(StrEnum):
    """Status of an individual pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    SKIPPED = "skipped"
    FAILED = "failed"


class SupportedValidationProfile(StrEnum):
    """Profiles registered in Phase 0/1 (coding only for v1 scope)."""

    CODING = "coding"


class OdooVersion(IntEnum):
    """Supported Odoo major versions for validation matrix."""

    V17 = 17
    V18 = 18
    V19 = 19


class ArtifactType(StrEnum):
    """Supported artifact kinds for Phase 2 (coding scope)."""

    BASE_MODEL = "base_model"
    CODING_ADAPTER = "coding_adapter"
    MERGED_MODEL = "merged_model"


class FingerprintPolicy(StrEnum):
    """Fingerprint verification strictness."""

    STRICT = "strict"
    WARN = "warn"
    OFF = "off"


class ArtifactResolutionErrorCode(StrEnum):
    """Structured artifact resolution error codes."""

    MISSING_PATH = "missing_path"
    INVALID_PATH = "invalid_path"
    UNSUPPORTED_ARTIFACT = "unsupported_artifact"
    MISSING_METADATA = "missing_metadata"
    INVALID_PROTOCOL = "invalid_protocol"
    DUPLICATE_ARTIFACT = "duplicate_artifact"
    INCOMPATIBLE_ARTIFACT = "incompatible_artifact"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"
    RESOLVER_FAILURE = "resolver_failure"


class InferenceLifecycleState(StrEnum):
    """Inference loading lifecycle states."""

    INITIALIZING = "initializing"
    LOADING_BASE = "loading_base"
    ATTACHING_ADAPTER = "attaching_adapter"
    VERIFYING = "verifying"
    READY = "ready"
    SHUTDOWN = "shutdown"


class InferenceErrorCode(StrEnum):
    """Structured inference error codes."""

    MISSING_BUNDLE = "missing_bundle"
    UNSUPPORTED_MODEL = "unsupported_model"
    UNSUPPORTED_ADAPTER = "unsupported_adapter"
    MODEL_LOAD_FAILURE = "model_load_failure"
    ADAPTER_LOAD_FAILURE = "adapter_load_failure"
    OOM = "oom"
    UNSUPPORTED_CONFIG = "unsupported_config"
    GENERATION_FAILURE = "generation_failure"
    NOT_INITIALIZED = "not_initialized"
    RUNNER_FAILURE = "runner_failure"

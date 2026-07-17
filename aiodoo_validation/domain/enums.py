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

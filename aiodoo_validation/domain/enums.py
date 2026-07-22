"""Domain enumerations for aiodoo-validation."""

from enum import IntEnum, StrEnum


class ExecutionTier(StrEnum):
    """Validation execution tier controlling pipeline depth."""

    SMOKE = "smoke"
    STANDARD = "standard"
    FULL = "full"
    # Alias accepted by normalize_execution_tier / CLI; stored as FULL internally.
    PROD = "prod"


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
    """Profiles supported by Validation Protocol V1."""

    CODING = "coding"
    PLANNER = "planner"
    REPAIR = "repair"
    CONVERSATION = "conversation"
    EXECUTION = "execution"
    APPROVAL = "approval"
    EVALUATION = "evaluation"


class ValidationKind(StrEnum):
    """Kind of validation performed by an oracle or scoring policy."""

    STRUCTURAL = "structural"
    BEHAVIORAL = "behavioral"


class ComparatorKind(StrEnum):
    """Registered comparator strategies for behavioral evaluation."""

    EXACT = "exact"
    NORMALIZED_TEXT = "normalized_text"
    AST = "ast"
    XML = "xml"
    JSON = "json"
    SEMANTIC = "semantic"
    TOKEN_SIMILARITY = "token_similarity"
    RULE_BASED = "rule_based"


class ScoreDimensionName(StrEnum):
    """Named score dimensions supported by production scoring architecture."""

    ORACLE = "oracle"
    BEHAVIOR = "behavior"
    SYNTAX = "syntax"
    STRUCTURAL = "structural"
    POLICY = "policy"
    WEIGHTED = "weighted"


class BehaviorStatus(StrEnum):
    """Lifecycle status for behavioral validation in a run."""

    NOT_AVAILABLE = "not_available"
    DEFERRED = "deferred"
    DISABLED = "disabled"
    SKIPPED = "skipped"
    ACTIVE = "active"
    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"


class CorpusRole(StrEnum):
    """Role of a behavioral evaluation corpus (Capability Delivery)."""

    TRAINING = "training"
    EVALUATION = "evaluation"
    SMOKE_FIXTURE = "smoke_fixture"


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


class ProfileErrorCode(StrEnum):
    """Structured profile resolution error codes."""

    UNSUPPORTED_PROFILE = "unsupported_profile"
    UNSUPPORTED_ADAPTER = "unsupported_adapter"
    UNSUPPORTED_MODEL = "unsupported_model"
    UNSUPPORTED_PROTOCOL = "unsupported_protocol"
    MISSING_BUNDLE = "missing_bundle"
    CAPABILITY_MISMATCH = "capability_mismatch"
    CONFIGURATION_ERROR = "configuration_error"
    PROFILE_CONSTRUCTION_FAILURE = "profile_construction_failure"


class OracleErrorCode(StrEnum):
    """Structured oracle framework error codes."""

    ORACLE_NOT_FOUND = "oracle_not_found"
    UNKNOWN_ORACLE = "unknown_oracle"
    REGISTRATION_FAILURE = "registration_failure"
    EXECUTION_FAILURE = "execution_failure"
    CONFIGURATION_FAILURE = "configuration_failure"
    PROFILE_MISMATCH = "profile_mismatch"
    CAPABILITY_MISMATCH = "capability_mismatch"
    MISSING_PLAN = "missing_plan"
    MISSING_PROFILE = "missing_profile"


class ScoreErrorCode(StrEnum):
    """Structured scoring engine error codes."""

    MISSING_ORACLE_RESULTS = "missing_oracle_results"
    MISSING_PLAN = "missing_plan"
    MISSING_PROFILE = "missing_profile"
    POLICY_NOT_FOUND = "policy_not_found"
    REGISTRATION_FAILURE = "registration_failure"
    CAPABILITY_MISMATCH = "capability_mismatch"
    PROFILE_MISMATCH = "profile_mismatch"
    EXECUTION_FAILURE = "execution_failure"
    CONFIGURATION_FAILURE = "configuration_failure"
    ORACLE_RESULT_MISSING = "oracle_result_missing"


class BenchmarkErrorCode(StrEnum):
    """Structured benchmark engine error codes."""

    MISSING_SCORE_RESULTS = "missing_score_results"
    MISSING_PLAN = "missing_plan"
    MISSING_PROFILE = "missing_profile"
    POLICY_NOT_FOUND = "policy_not_found"
    REGISTRATION_FAILURE = "registration_failure"
    CAPABILITY_MISMATCH = "capability_mismatch"
    PROFILE_MISMATCH = "profile_mismatch"
    EXECUTION_FAILURE = "execution_failure"
    CONFIGURATION_FAILURE = "configuration_failure"
    SCORE_RESULT_MISSING = "score_result_missing"


class CertificationErrorCode(StrEnum):
    """Structured certification engine error codes."""

    MISSING_BENCHMARK_RESULTS = "missing_benchmark_results"
    MISSING_PLAN = "missing_plan"
    MISSING_PROFILE = "missing_profile"
    POLICY_NOT_FOUND = "policy_not_found"
    REGISTRATION_FAILURE = "registration_failure"
    CAPABILITY_MISMATCH = "capability_mismatch"
    PROFILE_MISMATCH = "profile_mismatch"
    EXECUTION_FAILURE = "execution_failure"
    CONFIGURATION_FAILURE = "configuration_failure"
    BENCHMARK_RESULT_MISSING = "benchmark_result_missing"
    CONTRACT_VERSION_INCOMPATIBLE = "contract_version_incompatible"


class ReportErrorCode(StrEnum):
    """Structured report generator error codes."""

    MISSING_CERTIFICATION_RESULTS = "missing_certification_results"
    MISSING_PLAN = "missing_plan"
    MISSING_PROFILE = "missing_profile"
    TEMPLATE_NOT_FOUND = "template_not_found"
    REGISTRATION_FAILURE = "registration_failure"
    CAPABILITY_MISMATCH = "capability_mismatch"
    PROFILE_MISMATCH = "profile_mismatch"
    EXECUTION_FAILURE = "execution_failure"
    CONFIGURATION_FAILURE = "configuration_failure"
    CERTIFICATION_RESULT_MISSING = "certification_result_missing"

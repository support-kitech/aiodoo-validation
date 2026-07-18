"""Domain layer exports."""

from aiodoo_validation.domain.capability_record import (
    CapabilityArtifact,
    ParsedCapabilityRecord,
    TransformationDescriptor,
)
from aiodoo_validation.domain.capability_spec import (
    CapabilitySpecification,
    CorpusRequirements,
    RuntimeRequirements,
)
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.corpus import CorpusManifest
from aiodoo_validation.domain.enums import (
    CorpusRole,
    ExecutionTier,
    ExitStatus,
    OdooVersion,
    StageStatus,
    SupportedValidationProfile,
    ValidationStage,
)
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.domain.result import ValidationRunResult
from aiodoo_validation.domain.stage import PlaceholderStageResult, StageRecord

__all__ = [
    "CapabilityArtifact",
    "CapabilitySpecification",
    "CorpusManifest",
    "CorpusRequirements",
    "CorpusRole",
    "ExecutionTier",
    "ExitStatus",
    "OdooVersion",
    "ParsedCapabilityRecord",
    "PlaceholderStageResult",
    "RunContext",
    "RuntimeRequirements",
    "StageRecord",
    "StageStatus",
    "SupportedValidationProfile",
    "TransformationDescriptor",
    "ValidationRequest",
    "ValidationRunResult",
    "ValidationStage",
]

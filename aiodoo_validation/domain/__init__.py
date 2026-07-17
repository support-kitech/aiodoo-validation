"""Domain layer exports."""

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import (
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
    "ExecutionTier",
    "ExitStatus",
    "OdooVersion",
    "PlaceholderStageResult",
    "RunContext",
    "StageRecord",
    "StageStatus",
    "SupportedValidationProfile",
    "ValidationRequest",
    "ValidationRunResult",
    "ValidationStage",
]

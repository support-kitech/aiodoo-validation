"""Stage execution records and placeholder stage results."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import StageStatus, ValidationStage


@dataclass(frozen=True, slots=True)
class PlaceholderStageResult:
    """Stub result payload returned by Phase 0/1 stage implementations."""

    stage: ValidationStage
    status: StageStatus
    message: str
    data: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class StageRecord:
    """Immutable record of a single pipeline stage execution."""

    stage: ValidationStage
    status: StageStatus
    started_at: datetime
    ended_at: datetime | None
    message: str
    result: PlaceholderStageResult | None = None

    @property
    def duration_ms(self) -> int | None:
        if self.ended_at is None:
            return None
        delta = self.ended_at - self.started_at
        return int(delta.total_seconds() * 1000)

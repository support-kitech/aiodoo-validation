"""Immutable validation run context."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from aiodoo_validation.domain.enums import ExecutionTier, ExitStatus, StageStatus, ValidationStage
from aiodoo_validation.domain.request import SUPPORTED_PROTOCOL_MAJOR, ValidationRequest
from aiodoo_validation.domain.stage import PlaceholderStageResult, StageRecord


@dataclass(frozen=True, slots=True)
class RunContext:
    """
    Immutable run-scoped context flowing through the validation pipeline.

    Updates use ``with_*`` helpers returning new instances.
    """

    run_id: str
    protocol_major: int
    protocol_minor: int
    execution_tier: ExecutionTier
    request: ValidationRequest
    started_at: datetime
    current_stage: ValidationStage
    stage_records: tuple[StageRecord, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    placeholder_results: Mapping[ValidationStage, PlaceholderStageResult] = field(
        default_factory=lambda: MappingProxyType({})
    )
    exit_status: ExitStatus | None = None

    @staticmethod
    def begin(request: ValidationRequest) -> RunContext:
        run_id = request.run_id or f"run-{uuid4().hex[:12]}"
        return RunContext(
            run_id=run_id,
            protocol_major=SUPPORTED_PROTOCOL_MAJOR,
            protocol_minor=request.protocol_minor,
            execution_tier=request.execution_tier,
            request=request,
            started_at=datetime.now(UTC),
            current_stage=ValidationStage.LOAD_REQUEST,
        )

    def with_stage(self, stage: ValidationStage) -> RunContext:
        return replace(self, current_stage=stage)

    def with_stage_record(self, record: StageRecord) -> RunContext:
        return replace(self, stage_records=self.stage_records + (record,))

    def with_placeholder_result(self, result: PlaceholderStageResult) -> RunContext:
        updated = dict(self.placeholder_results)
        updated[result.stage] = result
        return replace(self, placeholder_results=MappingProxyType(updated))

    def with_metadata(self, **items: Any) -> RunContext:
        merged = {**dict(self.metadata), **items}
        return replace(self, metadata=MappingProxyType(merged))

    def with_error(self, message: str) -> RunContext:
        return replace(self, errors=self.errors + (message,))

    def with_warning(self, message: str) -> RunContext:
        return replace(self, warnings=self.warnings + (message,))

    def with_exit_status(self, status: ExitStatus) -> RunContext:
        return replace(self, exit_status=status)

    def stage_status(self, stage: ValidationStage) -> StageStatus:
        for record in reversed(self.stage_records):
            if record.stage == stage:
                return record.status
        return StageStatus.PENDING

"""ValidationRequest builders for ecosystem consumers (Phase 11)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aiodoo_validation.domain.enums import ExecutionTier, OdooVersion
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.execution import normalize_execution_tier


def parse_odoo_versions(raw: str) -> tuple[int, ...]:
    """Parse a comma-separated Odoo version list."""
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts:
        raise ValueError("odoo_versions must contain at least one version.")
    return tuple(int(part) for part in parts)


def build_approval_request(
    *,
    base_model_ref: str,
    adapter_ref: str,
    merged_model_ref: str | None = None,
    execution_tier: ExecutionTier | str = ExecutionTier.STANDARD,
    odoo_versions: tuple[int, ...] | str = (
        OdooVersion.V17,
        OdooVersion.V18,
        OdooVersion.V19,
    ),
    run_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ValidationRequest:
    """Build an approval profile ``ValidationRequest``."""
    tier = normalize_execution_tier(execution_tier)
    if isinstance(odoo_versions, str):
        versions = parse_odoo_versions(odoo_versions)
    else:
        versions = odoo_versions
    return ValidationRequest(
        profile_name="approval",
        base_model_ref=base_model_ref,
        adapter_ref=adapter_ref,
        merged_model_ref=merged_model_ref,
        execution_tier=tier,
        odoo_versions=versions,
        run_id=run_id,
        metadata={} if metadata is None else metadata,
    )


def build_coding_request(
    *,
    base_model_ref: str,
    adapter_ref: str,
    merged_model_ref: str | None = None,
    execution_tier: ExecutionTier | str = ExecutionTier.STANDARD,
    odoo_versions: tuple[int, ...] | str = (
        OdooVersion.V17,
        OdooVersion.V18,
        OdooVersion.V19,
    ),
    run_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ValidationRequest:
    """Build a coding profile ``ValidationRequest``."""
    tier = normalize_execution_tier(execution_tier)
    if isinstance(odoo_versions, str):
        versions = parse_odoo_versions(odoo_versions)
    else:
        versions = odoo_versions
    return ValidationRequest(
        profile_name="coding",
        base_model_ref=base_model_ref,
        adapter_ref=adapter_ref,
        merged_model_ref=merged_model_ref,
        execution_tier=tier,
        odoo_versions=versions,
        run_id=run_id,
        metadata={} if metadata is None else metadata,
    )


def build_conversation_request(
    *,
    base_model_ref: str,
    adapter_ref: str,
    merged_model_ref: str | None = None,
    execution_tier: ExecutionTier | str = ExecutionTier.STANDARD,
    odoo_versions: tuple[int, ...] | str = (
        OdooVersion.V17,
        OdooVersion.V18,
        OdooVersion.V19,
    ),
    run_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ValidationRequest:
    """Build a conversation profile ``ValidationRequest``."""
    tier = normalize_execution_tier(execution_tier)
    if isinstance(odoo_versions, str):
        versions = parse_odoo_versions(odoo_versions)
    else:
        versions = odoo_versions
    return ValidationRequest(
        profile_name="conversation",
        base_model_ref=base_model_ref,
        adapter_ref=adapter_ref,
        merged_model_ref=merged_model_ref,
        execution_tier=tier,
        odoo_versions=versions,
        run_id=run_id,
        metadata={} if metadata is None else metadata,
    )


def build_evaluation_request(
    *,
    base_model_ref: str,
    adapter_ref: str,
    merged_model_ref: str | None = None,
    execution_tier: ExecutionTier | str = ExecutionTier.STANDARD,
    odoo_versions: tuple[int, ...] | str = (
        OdooVersion.V17,
        OdooVersion.V18,
        OdooVersion.V19,
    ),
    run_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ValidationRequest:
    """Build an evaluation profile ``ValidationRequest``."""
    tier = normalize_execution_tier(execution_tier)
    if isinstance(odoo_versions, str):
        versions = parse_odoo_versions(odoo_versions)
    else:
        versions = odoo_versions
    return ValidationRequest(
        profile_name="evaluation",
        base_model_ref=base_model_ref,
        adapter_ref=adapter_ref,
        merged_model_ref=merged_model_ref,
        execution_tier=tier,
        odoo_versions=versions,
        run_id=run_id,
        metadata={} if metadata is None else metadata,
    )


def build_execution_request(
    *,
    base_model_ref: str,
    adapter_ref: str,
    merged_model_ref: str | None = None,
    execution_tier: ExecutionTier | str = ExecutionTier.STANDARD,
    odoo_versions: tuple[int, ...] | str = (
        OdooVersion.V17,
        OdooVersion.V18,
        OdooVersion.V19,
    ),
    run_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ValidationRequest:
    """Build an execution profile ``ValidationRequest``."""
    tier = normalize_execution_tier(execution_tier)
    if isinstance(odoo_versions, str):
        versions = parse_odoo_versions(odoo_versions)
    else:
        versions = odoo_versions
    return ValidationRequest(
        profile_name="execution",
        base_model_ref=base_model_ref,
        adapter_ref=adapter_ref,
        merged_model_ref=merged_model_ref,
        execution_tier=tier,
        odoo_versions=versions,
        run_id=run_id,
        metadata={} if metadata is None else metadata,
    )


def build_planner_request(
    *,
    base_model_ref: str,
    adapter_ref: str,
    merged_model_ref: str | None = None,
    execution_tier: ExecutionTier | str = ExecutionTier.STANDARD,
    odoo_versions: tuple[int, ...] | str = (
        OdooVersion.V17,
        OdooVersion.V18,
        OdooVersion.V19,
    ),
    run_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ValidationRequest:
    """Build a planner profile ``ValidationRequest``."""
    tier = normalize_execution_tier(execution_tier)
    if isinstance(odoo_versions, str):
        versions = parse_odoo_versions(odoo_versions)
    else:
        versions = odoo_versions
    return ValidationRequest(
        profile_name="planner",
        base_model_ref=base_model_ref,
        adapter_ref=adapter_ref,
        merged_model_ref=merged_model_ref,
        execution_tier=tier,
        odoo_versions=versions,
        run_id=run_id,
        metadata={} if metadata is None else metadata,
    )

"""ValidationRequest builders for ecosystem consumers (Phase 11)."""

from __future__ import annotations

from aiodoo_validation.domain.enums import ExecutionTier, OdooVersion
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.execution import normalize_execution_tier


def parse_odoo_versions(raw: str) -> tuple[int, ...]:
    """Parse a comma-separated Odoo version list."""
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts:
        raise ValueError("odoo_versions must contain at least one version.")
    return tuple(int(part) for part in parts)


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
    )

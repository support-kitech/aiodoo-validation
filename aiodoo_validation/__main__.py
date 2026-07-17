"""Run a placeholder validation lifecycle (Phase 0/1 development entry)."""

from __future__ import annotations

import sys

from aiodoo_validation.domain.enums import ExecutionTier, SupportedValidationProfile
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.engine import ValidationEngine


def main() -> int:
    """Execute a stub validation run with placeholder artifact references."""
    engine = ValidationEngine.with_stubs()
    request = ValidationRequest(
        profile_name=SupportedValidationProfile.CODING.value,
        base_model_ref="Qwen/Qwen3-8B",
        adapter_ref="artifacts/adapters/EXP-0001/stub",
        execution_tier=ExecutionTier.SMOKE,
    )
    result = engine.run(request)
    print(f"exit_status={result.exit_status.value}")
    print(f"run_id={result.run_context.run_id}")
    print(f"stages_executed={len(result.run_context.stage_records)}")
    if result.exit_status.value in {"invalid_request", "internal_error", "failed"}:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

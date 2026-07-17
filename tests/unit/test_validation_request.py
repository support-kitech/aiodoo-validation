"""Unit tests for ValidationRequest."""

import pytest

from aiodoo_validation.domain.enums import ExecutionTier, SupportedValidationProfile
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.exceptions import InvalidRequestError


def test_valid_coding_request() -> None:
    request = ValidationRequest(
        profile_name=SupportedValidationProfile.CODING.value,
        base_model_ref="Qwen/Qwen3-8B",
        adapter_ref="artifacts/adapters/EXP-0001/stub",
        execution_tier=ExecutionTier.SMOKE,
    )
    assert request.profile_name == "coding"
    assert request.protocol_major == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"profile_name": "", "base_model_ref": "base", "adapter_ref": "adapter"},
        {
            "profile_name": "planner",
            "base_model_ref": "base",
            "adapter_ref": "adapter",
        },
        {
            "profile_name": "coding",
            "base_model_ref": "",
            "adapter_ref": "adapter",
        },
        {
            "profile_name": "coding",
            "base_model_ref": "base",
            "adapter_ref": "",
        },
        {
            "profile_name": "coding",
            "base_model_ref": "base",
            "adapter_ref": "adapter",
            "protocol_major": 2,
        },
        {
            "profile_name": "coding",
            "base_model_ref": "base",
            "adapter_ref": "adapter",
            "odoo_versions": (20,),
        },
        {
            "profile_name": "coding",
            "base_model_ref": "base",
            "adapter_ref": "adapter",
            "odoo_versions": (),
        },
    ],
)
def test_invalid_request_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises(InvalidRequestError):
        ValidationRequest(**kwargs)  # type: ignore[arg-type]

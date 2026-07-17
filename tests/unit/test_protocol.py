"""Unit tests for Validation Protocol negotiation."""

import pytest

from aiodoo_validation.domain.enums import SupportedValidationProfile
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.engine.protocol import negotiate_protocol
from aiodoo_validation.exceptions import InvalidRequestError


def test_negotiate_protocol_v1() -> None:
    request = ValidationRequest(
        profile_name=SupportedValidationProfile.CODING.value,
        base_model_ref="base",
        adapter_ref="adapter",
        protocol_minor=2,
    )
    assert negotiate_protocol(request) == (1, 2)


def test_negotiate_protocol_rejects_unsupported_major_at_construction() -> None:
    with pytest.raises(InvalidRequestError):
        ValidationRequest(
            profile_name=SupportedValidationProfile.CODING.value,
            base_model_ref="base",
            adapter_ref="adapter",
            protocol_major=2,
        )

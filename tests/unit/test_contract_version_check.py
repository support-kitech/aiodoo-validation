"""Unit tests for the certification contract-version compatibility gate."""

from __future__ import annotations

import pytest
from aiodoo_contract.version import CONTRACT_VERSION

from aiodoo_validation.contract.version_check import (
    VALIDATION_CONTRACT_VERSION,
    ContractVersionError,
    ensure_contract_compatible,
)


def test_validation_pin_is_compatible_with_installed_contract() -> None:
    result = ensure_contract_compatible()
    assert result.is_compatible is True
    assert str(result.contract_version) == CONTRACT_VERSION


def test_default_consumer_version_matches_pin() -> None:
    result = ensure_contract_compatible(consumer_version=VALIDATION_CONTRACT_VERSION)
    assert result.is_compatible is True


def test_incompatible_major_version_raises() -> None:
    with pytest.raises(ContractVersionError, match="incompatible"):
        ensure_contract_compatible(consumer_version="999.0.0")


def test_incompatible_newer_minor_version_raises() -> None:
    major = CONTRACT_VERSION.split(".")[0]
    newer_minor = f"{major}.9999.0"
    with pytest.raises(ContractVersionError, match="incompatible"):
        ensure_contract_compatible(consumer_version=newer_minor)


def test_error_message_references_pin_and_installed_version() -> None:
    with pytest.raises(ContractVersionError) as exc_info:
        ensure_contract_compatible(consumer_version="999.0.0")
    message = str(exc_info.value)
    assert "999.0.0" in message
    assert CONTRACT_VERSION in message

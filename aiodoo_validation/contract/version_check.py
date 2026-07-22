"""Capability Contract version compatibility gate for aiodoo-validation.

Validation pins :data:`VALIDATION_CONTRACT_VERSION` — the Capability
Contract version its prompt/schema/parser/template integration was built
and tested against (ADR-0009 in aiodoo-contract). Certification calls
:func:`ensure_contract_compatible` before executing any certification
policy and fails closed, rather than certifying an adapter against a
contract version whose schemas, prompts, parsers, or templates may have
moved out from under the assumptions this integration was validated
against.
"""

from __future__ import annotations

from aiodoo_contract.version import CompatibilityResult, check_compatibility

from aiodoo_validation.exceptions import AiodooValidationError

__all__ = [
    "VALIDATION_CONTRACT_VERSION",
    "ContractVersionError",
    "ensure_contract_compatible",
]

#: The Capability Contract version aiodoo-validation's contract integration
#: (prompts, chat templates, schemas, parsers, validators) is pinned to.
#: Bump deliberately when adopting a new contract release — never let this
#: silently drift from what was actually validated against.
VALIDATION_CONTRACT_VERSION = "1.0.0"


class ContractVersionError(AiodooValidationError):
    """Raised when the installed `aiodoo_contract` is incompatible with validation's pin."""


def ensure_contract_compatible(
    *,
    consumer_version: str = VALIDATION_CONTRACT_VERSION,
) -> CompatibilityResult:
    """Verify the installed ``aiodoo_contract`` is compatible with ``consumer_version``.

    Returns:
        The :class:`~aiodoo_contract.version.CompatibilityResult` on success
        (``COMPATIBLE``).

    Raises:
        ContractVersionError: if the installed contract is a different
            major version, or a strictly older minor version than
            ``consumer_version`` expects (``MINOR_MISMATCH``) — validation
            (and certification specifically) must fail early rather than
            certify against prompts/schemas/parsers the installed contract
            does not actually provide.
    """
    result = check_compatibility(consumer_version)
    if not result.is_compatible:
        raise ContractVersionError(
            "aiodoo-validation is incompatible with the installed aiodoo_contract: "
            f"{result.reason} (validation pinned to {consumer_version!r}, "
            f"installed contract is {result.contract_version!s}). "
            "Upgrade/downgrade aiodoo_contract or update "
            "aiodoo_validation.contract.version_check.VALIDATION_CONTRACT_VERSION "
            "after re-validating the contract integration."
        )
    return result

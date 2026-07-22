"""Bridge raw behavioral-inference output into canonical `aiodoo_contract` responses.

This is the only place in aiodoo-validation that interprets model-generated
text for a contract-mapped capability. It delegates decoding to
``aiodoo_contract.parsers`` (ADR-0006) and structural/capability agreement
checking to ``aiodoo_contract.validators`` (ADR-0007) — the exact same
parser and validator classes ``aiodoo-core``'s runtime agent loop will use
to interpret the same model's output. Behavioral validation must never
diverge from that interpretation; see ``CONTRACT_ADOPTION.md``.

Deliberately fail-closed: :func:`parse_capability_output` raises
:class:`ContractParseError` (never returns a partial/best-effort result) on
any decoding or validation failure, so callers treat "the model did not
produce a contract-conformant response" as an explicit behavioral failure
rather than silently falling through to a raw-text comparison that could
mask the defect.
"""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_contract.parsers import CapabilityParser, MalformedOutputError
from aiodoo_contract.schemas.approval import ApprovalResponse
from aiodoo_contract.schemas.base import CapabilityResponse
from aiodoo_contract.schemas.coding import CodingResponse
from aiodoo_contract.schemas.conversation import ConversationResponse
from aiodoo_contract.schemas.enums import CapabilityName
from aiodoo_contract.schemas.execution import ExecutionResponse
from aiodoo_contract.schemas.planner import PlannerResponse
from aiodoo_contract.schemas.registry import response_schema_for
from aiodoo_contract.schemas.repair import RepairResponse
from aiodoo_contract.validators import ContractValidator

from aiodoo_validation.contract.adapters import SUPPORTED_CAPABILITIES

__all__ = [
    "ContractParseError",
    "ParsedContractOutput",
    "extract_comparable_text",
    "is_contract_mapped_capability",
    "parse_capability_output",
]


class ContractParseError(ValueError):
    """Raised when model output cannot be parsed/validated against the contract.

    Callers treat this as a fail-closed behavioral finding
    (``contract_parse_failed`` / ``contract_response_invalid``), never as a
    silent fallback to comparing raw, unparsed text.
    """


@dataclass(frozen=True, slots=True)
class ParsedContractOutput:
    """A model output successfully decoded into a canonical contract response."""

    capability: CapabilityName
    response: CapabilityResponse
    comparable_text: str


def is_contract_mapped_capability(capability_id: str) -> bool:
    """``True`` if ``capability_id`` has a canonical contract projection.

    ``evaluation`` (and any future capability without a
    :mod:`aiodoo_validation.contract.adapters` projector) returns ``False``
    — behavioral validation for those capabilities continues to compare raw
    generated text directly, exactly as before contract adoption.
    """
    return capability_id in SUPPORTED_CAPABILITIES


def parse_capability_output(capability_id: str, raw_text: str) -> ParsedContractOutput:
    """Parse and validate ``raw_text`` as ``capability_id``'s canonical response.

    Raises:
        ContractParseError: if ``capability_id`` is not a recognized
            :class:`~aiodoo_contract.schemas.enums.CapabilityName`, ``raw_text``
            is not valid JSON, the parsed JSON does not match the
            capability's registered response schema, or the parsed response
            fails :class:`~aiodoo_contract.validators.ContractValidator`
            (version/capability-class agreement).
    """
    try:
        capability = CapabilityName(capability_id)
    except ValueError as exc:
        raise ContractParseError(
            f"{capability_id!r} is not a recognized aiodoo_contract capability."
        ) from exc

    schema = response_schema_for(capability)
    try:
        response = CapabilityParser(schema).parse(raw_text)
    except MalformedOutputError as exc:
        raise ContractParseError(
            f"model output for capability {capability_id!r} did not parse as "
            f"{schema.__name__}: {exc}"
        ) from exc

    validation = ContractValidator().validate_response(response)
    if not validation.valid:
        issues = "; ".join(f"{issue.path}: {issue.message}" for issue in validation.issues)
        raise ContractParseError(
            f"parsed {schema.__name__} for capability {capability_id!r} failed contract "
            f"validation: {issues}"
        )

    return ParsedContractOutput(
        capability=capability,
        response=response,
        comparable_text=extract_comparable_text(response),
    )


def extract_comparable_text(response: CapabilityResponse) -> str:
    """Extract the text existing (pre-contract) comparators should compare.

    Each capability's response is structured differently — this is the one
    place that knows how to reduce a canonical
    :class:`~aiodoo_contract.schemas.base.CapabilityResponse` back down to
    the plain text ``ExpectedOutput``/``GeneratedOutput`` comparators
    (:mod:`aiodoo_validation.comparators`) operate on, so contract adoption
    does not require rewriting every comparator.

    Raises:
        ContractParseError: if ``response`` is not one of the response
            schemas registered in
            :data:`aiodoo_validation.contract.adapters.SUPPORTED_CAPABILITIES`.
    """
    if isinstance(response, CodingResponse):
        return "\n".join(edit.content for edit in response.edits)
    if isinstance(response, RepairResponse):
        return "\n".join(edit.content for edit in response.fix.edits)
    if isinstance(response, PlannerResponse):
        return "\n".join(step.description for step in response.steps)
    if isinstance(response, ExecutionResponse):
        return response.stdout
    if isinstance(response, ConversationResponse):
        return response.reply.content
    if isinstance(response, ApprovalResponse):
        return response.reason if response.reason else response.status.value
    raise ContractParseError(
        f"no comparable-text extractor registered for response type {type(response).__name__}."
    )

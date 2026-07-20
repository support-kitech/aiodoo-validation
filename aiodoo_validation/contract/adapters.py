"""Project a `ParsedCapabilityRecord` onto its canonical `aiodoo_contract` shape.

``ParsedCapabilityRecord`` (:mod:`aiodoo_validation.domain.capability_record`)
is validation's own capability-agnostic normalization of a corpus record —
produced by each capability's ``CapabilityRecordParser`` regardless of
whether the underlying record originated from a native validation fixture
or from an ``aiodoo-datasets`` evaluation corpus. It intentionally carries
no capability-specific schema fields (no ``instruction``, no ``goal``, no
``fix`` — just ``problem`` / ``artifacts`` / ``explanation`` / ``tags`` /
``metadata``), so projecting it onto ``aiodoo_contract.schemas`` requires
one small, capability-specific mapping function per capability — the same
shape of adapter aiodoo-training's ``aiodoo_training/contract/adapters.py``
implements for its own (richer) dataset record shape.

Every ``project_*`` function raises :class:`ContractAdapterError` (never a
bare ``KeyError``/``TypeError``/pydantic ``ValidationError``) when a record
cannot be projected, so callers can treat "this record does not have enough
structure to build a contract-shaped request/response" as a distinct,
expected, fail-closed outcome rather than a crash.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from aiodoo_contract.schemas.approval import ApprovalRequest, ApprovalResponse
from aiodoo_contract.schemas.base import CapabilityRequest, CapabilityResponse
from aiodoo_contract.schemas.coding import CodingRequest, CodingResponse, FileEdit
from aiodoo_contract.schemas.conversation import (
    ConversationRequest,
    ConversationResponse,
    ConversationTurn,
)
from aiodoo_contract.schemas.enums import ApprovalStatus, ConversationRole, ExecutionStatus
from aiodoo_contract.schemas.execution import ExecutionRequest, ExecutionResponse
from aiodoo_contract.schemas.planner import PlannerRequest, PlannerResponse, PlanStep
from aiodoo_contract.schemas.repair import RepairFix, RepairRequest, RepairResponse
from pydantic import ValidationError as PydanticValidationError

from aiodoo_validation.domain.capability_record import CapabilityArtifact, ParsedCapabilityRecord

__all__ = [
    "SUPPORTED_CAPABILITIES",
    "ContractAdapterError",
    "ContractProjection",
    "project_approval",
    "project_coding",
    "project_conversation",
    "project_execution",
    "project_planner",
    "project_record",
    "project_repair",
]

_ROLE_KEY = "snapshot_role"
_ROLE_ORIGINAL = "original"
_ROLE_EXPECTED = "expected"


class ContractAdapterError(ValueError):
    """A ``ParsedCapabilityRecord`` does not carry enough structure to project.

    This is an expected, recoverable outcome — callers (the behavior
    pipeline) catch this specifically and fail the case closed rather than
    letting it propagate as a bare ``KeyError``/``TypeError``.
    """


@dataclass(frozen=True, slots=True)
class ContractProjection:
    """A record's canonical ``aiodoo_contract`` request/response projection."""

    capability: str
    request: CapabilityRequest
    response: CapabilityResponse


def _artifact_role(artifact: CapabilityArtifact) -> str:
    raw = artifact.metadata.get(_ROLE_KEY, _ROLE_ORIGINAL)
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return _ROLE_ORIGINAL


def _contents_by_role(record: ParsedCapabilityRecord, *, role: str) -> dict[str, str]:
    return {
        artifact.path: artifact.content
        for artifact in record.artifacts
        if _artifact_role(artifact) == role
    }


def _edit_contents(record: ParsedCapabilityRecord) -> dict[str, str]:
    """Prefer expected-role artifact contents; fall back to original-role.

    Mirrors :meth:`aiodoo_validation.behavior.case_builder.BehaviorCaseBuilder._expected_text`'s
    preference order: gold content is whatever the record declares as
    ``expected``, or the untouched original when no gold snapshot exists
    (gold expressed purely as transformations, verified separately by
    :class:`~aiodoo_validation.behavior.capability_pipeline.CapabilityBehaviorPipeline`).
    """
    expected = _contents_by_role(record, role=_ROLE_EXPECTED)
    if expected:
        return expected
    return _contents_by_role(record, role=_ROLE_ORIGINAL)


def _edits_from_contents(contents: Mapping[str, str]) -> list[FileEdit]:
    return [FileEdit(path=path, content=contents[path]) for path in sorted(contents)]


def _primary_text(record: ParsedCapabilityRecord, *, label: str) -> str:
    """The record's primary instruction/goal/failure-description text.

    ``problem`` may legitimately be empty for artifact-only records (see
    :class:`ParsedCapabilityRecord`'s docstring) — every contract request
    schema requires a non-empty instruction-shaped field, so an empty
    ``problem`` falls back to ``explanation`` before giving up.
    """
    if record.problem.strip():
        return record.problem
    if record.explanation and record.explanation.strip():
        return record.explanation
    raise ContractAdapterError(
        f"{label} record {record.record_id!r} has neither a usable 'problem' nor 'explanation'."
    )


def _wrap_validation_error(exc: PydanticValidationError, *, label: str) -> ContractAdapterError:
    return ContractAdapterError(f"{label} projection failed schema validation: {exc}")


# ---------------------------------------------------------------------
# Coding
# ---------------------------------------------------------------------


def project_coding(record: ParsedCapabilityRecord) -> ContractProjection:
    """Project a coding ``ParsedCapabilityRecord`` onto Coding Request/Response."""
    instruction = _primary_text(record, label="coding")
    edits = _edits_from_contents(_edit_contents(record))
    if not edits:
        raise ContractAdapterError(
            f"coding record {record.record_id!r} has no artifacts to project into edits."
        )
    constraints_raw = record.metadata.get("constraints")
    constraints = (
        [str(item) for item in constraints_raw] if isinstance(constraints_raw, list) else []
    )
    try:
        request = CodingRequest(instruction=instruction, constraints=constraints)
        response = CodingResponse(
            request_id=request.request_id,
            edits=edits,
            rationale=record.explanation,
        )
    except PydanticValidationError as exc:
        raise _wrap_validation_error(exc, label="coding") from exc
    return ContractProjection("coding", request, response)


# ---------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------


def project_planner(record: ParsedCapabilityRecord) -> ContractProjection:
    """Project a planner ``ParsedCapabilityRecord`` onto Planner Request/Response.

    ``ParsedCapabilityRecord`` has no native multi-step plan representation
    — it is a single ``problem``/``explanation`` pair, not a list of steps.
    A single :class:`PlanStep` is synthesized from ``explanation`` (the
    intended outcome) when present, falling back to ``problem``. This is a
    documented, intentional simplification (see ``CONTRACT_ADOPTION.md``),
    not a claim that planner corpora only ever have one step.
    """
    goal = _primary_text(record, label="planner")
    description = record.explanation if record.explanation and record.explanation.strip() else goal
    try:
        request = PlannerRequest(goal=goal)
        response = PlannerResponse(
            request_id=request.request_id,
            steps=[PlanStep(index=0, description=description)],
        )
    except PydanticValidationError as exc:
        raise _wrap_validation_error(exc, label="planner") from exc
    return ContractProjection("planner", request, response)


# ---------------------------------------------------------------------
# Repair
# ---------------------------------------------------------------------


def project_repair(record: ParsedCapabilityRecord) -> ContractProjection:
    """Project a repair ``ParsedCapabilityRecord`` onto Repair Request/Response."""
    failure_description = _primary_text(record, label="repair")
    edits = _edits_from_contents(_edit_contents(record))
    if not edits:
        raise ContractAdapterError(
            f"repair record {record.record_id!r} has no artifacts to project a fix onto."
        )
    fix_description = (
        record.explanation
        if record.explanation and record.explanation.strip()
        else failure_description
    )
    try:
        request = RepairRequest(failure_description=failure_description)
        response = RepairResponse(
            request_id=request.request_id,
            fix=RepairFix(description=fix_description, edits=edits, confidence=0.75),
        )
    except PydanticValidationError as exc:
        raise _wrap_validation_error(exc, label="repair") from exc
    return ContractProjection("repair", request, response)


# ---------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------


def project_execution(record: ParsedCapabilityRecord) -> ContractProjection:
    """Project an execution ``ParsedCapabilityRecord`` onto Execution Request/Response."""
    command = _primary_text(record, label="execution")
    stdout = record.explanation or ""
    try:
        request = ExecutionRequest(command=command)
        response = ExecutionResponse(
            request_id=request.request_id,
            status=ExecutionStatus.SUCCEEDED,
            exit_code=0,
            stdout=stdout,
        )
    except PydanticValidationError as exc:
        raise _wrap_validation_error(exc, label="execution") from exc
    return ContractProjection("execution", request, response)


# ---------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------


def project_conversation(record: ParsedCapabilityRecord) -> ContractProjection:
    """Project a conversation ``ParsedCapabilityRecord`` onto Conversation Request/Response."""
    user_text = _primary_text(record, label="conversation")
    reply_text = (
        record.explanation if record.explanation and record.explanation.strip() else user_text
    )
    try:
        request = ConversationRequest(
            turns=[ConversationTurn(role=ConversationRole.USER, content=user_text)]
        )
        response = ConversationResponse(
            request_id=request.request_id,
            reply=ConversationTurn(role=ConversationRole.ASSISTANT, content=reply_text),
        )
    except PydanticValidationError as exc:
        raise _wrap_validation_error(exc, label="conversation") from exc
    return ContractProjection("conversation", request, response)


# ---------------------------------------------------------------------
# Approval
# ---------------------------------------------------------------------


def project_approval(record: ParsedCapabilityRecord) -> ContractProjection:
    """Project an approval ``ParsedCapabilityRecord`` onto Approval Request/Response.

    ``ParsedCapabilityRecord`` has no native decision/status field —
    validation's approval corpora express the decision as ``explanation``
    text, not a structured verdict. The projected response is always
    ``APPROVED`` with ``explanation`` as the reason: a documented
    simplification, not a claim the source record encodes a rejection.
    """
    subject = _primary_text(record, label="approval")
    try:
        request = ApprovalRequest(subject=subject)
        response = ApprovalResponse(
            request_id=request.request_id,
            status=ApprovalStatus.APPROVED,
            reason=record.explanation,
        )
    except PydanticValidationError as exc:
        raise _wrap_validation_error(exc, label="approval") from exc
    return ContractProjection("approval", request, response)


# ---------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------

_PROJECTORS: dict[str, Callable[[ParsedCapabilityRecord], ContractProjection]] = {
    "coding": project_coding,
    "planner": project_planner,
    "repair": project_repair,
    "execution": project_execution,
    "conversation": project_conversation,
    "approval": project_approval,
}

#: Capabilities with a canonical `aiodoo_contract` projection from
#: ``ParsedCapabilityRecord``. ``evaluation`` has no projection here — the
#: same intentional gap ``aiodoo-datasets`` and ``aiodoo-training`` document
#: in their own adapter modules: ``EvaluationRequest``/``Response`` model
#: judging *another* capability's request/response pair, which
#: ``ParsedCapabilityRecord`` (a single problem/artifact record) does not
#: carry enough structure to reconstruct.
SUPPORTED_CAPABILITIES: tuple[str, ...] = tuple(_PROJECTORS)


def project_record(record: ParsedCapabilityRecord) -> ContractProjection:
    """Project ``record`` onto its canonical contract shape.

    Raises:
        ContractAdapterError: if ``record.capability_id`` is not one of
            :data:`SUPPORTED_CAPABILITIES`, or the record cannot be
            projected onto that capability's contract shape.
    """
    projector = _PROJECTORS.get(record.capability_id)
    if projector is None:
        raise ContractAdapterError(
            f"no contract adapter registered for capability {record.capability_id!r}; "
            f"supported: {SUPPORTED_CAPABILITIES}"
        )
    return projector(record)

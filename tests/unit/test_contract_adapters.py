"""Unit tests for the ParsedCapabilityRecord -> aiodoo_contract projection layer."""

from __future__ import annotations

import pytest
from aiodoo_contract.schemas.approval import ApprovalRequest, ApprovalResponse
from aiodoo_contract.schemas.coding import CodingRequest, CodingResponse
from aiodoo_contract.schemas.conversation import ConversationRequest, ConversationResponse
from aiodoo_contract.schemas.execution import ExecutionRequest, ExecutionResponse
from aiodoo_contract.schemas.planner import PlannerRequest, PlannerResponse
from aiodoo_contract.schemas.repair import RepairRequest, RepairResponse

from aiodoo_validation.contract.adapters import (
    SUPPORTED_CAPABILITIES,
    ContractAdapterError,
    project_record,
)
from aiodoo_validation.domain.capability_record import CapabilityArtifact, ParsedCapabilityRecord


def _record(
    *,
    capability_id: str,
    problem: str = "",
    explanation: str | None = None,
    artifacts: tuple[CapabilityArtifact, ...] = (),
) -> ParsedCapabilityRecord:
    return ParsedCapabilityRecord(
        record_id=f"{capability_id}.record",
        capability_id=capability_id,
        problem=problem,
        artifacts=artifacts,
        explanation=explanation,
    )


def _artifact(path: str, content: str, *, role: str = "original") -> CapabilityArtifact:
    return CapabilityArtifact(
        artifact_id=f"a-{path}-{role}",
        path=path,
        content=content,
        metadata={"snapshot_role": role},
    )


def test_supported_capabilities_excludes_evaluation() -> None:
    assert "evaluation" not in SUPPORTED_CAPABILITIES
    assert set(SUPPORTED_CAPABILITIES) == {
        "coding",
        "planner",
        "repair",
        "execution",
        "conversation",
        "approval",
    }


def test_project_record_unknown_capability_raises() -> None:
    record = _record(capability_id="evaluation", problem="judge this")
    with pytest.raises(ContractAdapterError, match="no contract adapter registered"):
        project_record(record)


class TestCodingProjection:
    def test_projects_request_and_response(self) -> None:
        record = _record(
            capability_id="coding",
            problem="Rename the field label.",
            explanation="Update Char field label.",
            artifacts=(_artifact("models/sale.py", "name = fields.Char(string='Old')\n"),),
        )
        projection = project_record(record)
        assert projection.capability == "coding"
        assert isinstance(projection.request, CodingRequest)
        assert isinstance(projection.response, CodingResponse)
        assert projection.request.instruction == "Rename the field label."
        assert projection.response.request_id == projection.request.request_id
        assert projection.response.edits[0].path == "models/sale.py"
        assert projection.response.rationale == "Update Char field label."

    def test_prefers_expected_role_artifacts_for_edits(self) -> None:
        record = _record(
            capability_id="coding",
            problem="Add partner helper.",
            artifacts=(
                _artifact("models/partner.py", "original content\n", role="original"),
                _artifact("models/partner.py", "expected content\n", role="expected"),
            ),
        )
        projection = project_record(record)
        assert isinstance(projection.response, CodingResponse)
        # `FileEdit.content` strips surrounding whitespace (ADR-0007's
        # ``ContractModel`` sets ``str_strip_whitespace=True``) — this is a
        # contract-wide normalization, not something the adapter opts into.
        assert [edit.content for edit in projection.response.edits] == ["expected content"]

    def test_no_artifacts_raises_adapter_error(self) -> None:
        record = _record(capability_id="coding", problem="Do something.")
        with pytest.raises(ContractAdapterError, match="no artifacts to project"):
            project_record(record)

    def test_empty_problem_falls_back_to_explanation(self) -> None:
        record = _record(
            capability_id="coding",
            problem="",
            explanation="Fix the thing.",
            artifacts=(_artifact("a.py", "x = 1\n"),),
        )
        projection = project_record(record)
        assert projection.request.instruction == "Fix the thing."

    def test_no_problem_or_explanation_raises(self) -> None:
        record = _record(
            capability_id="coding",
            problem="",
            artifacts=(_artifact("a.py", "x = 1\n"),),
        )
        with pytest.raises(ContractAdapterError, match="neither a usable"):
            project_record(record)


class TestPlannerProjection:
    def test_projects_single_synthesized_step(self) -> None:
        record = _record(
            capability_id="planner",
            problem="Rename the plan step label.",
            explanation="Update plan step label.",
        )
        projection = project_record(record)
        assert isinstance(projection.request, PlannerRequest)
        assert isinstance(projection.response, PlannerResponse)
        assert projection.request.goal == "Rename the plan step label."
        assert projection.response.steps[0].description == "Update plan step label."
        assert projection.response.steps[0].index == 0


class TestRepairProjection:
    def test_projects_fix_from_artifacts(self) -> None:
        record = _record(
            capability_id="repair",
            problem="Use sudo for SQL execute",
            explanation="Direct SQL should use sudo when intentional.",
            artifacts=(_artifact("models/mod.py", "cr.execute(query)\n"),),
        )
        projection = project_record(record)
        assert isinstance(projection.request, RepairRequest)
        assert isinstance(projection.response, RepairResponse)
        assert projection.response.fix.description == "Direct SQL should use sudo when intentional."
        assert 0.0 <= projection.response.fix.confidence <= 1.0

    def test_no_artifacts_raises_adapter_error(self) -> None:
        record = _record(capability_id="repair", problem="Something broke.")
        with pytest.raises(ContractAdapterError, match="no artifacts to project a fix"):
            project_record(record)


class TestExecutionProjection:
    def test_projects_command_and_stdout(self) -> None:
        record = _record(
            capability_id="execution",
            problem="Run the migration.",
            explanation="Migration completed.",
        )
        projection = project_record(record)
        assert isinstance(projection.request, ExecutionRequest)
        assert isinstance(projection.response, ExecutionResponse)
        assert projection.request.command == "Run the migration."
        assert projection.response.stdout == "Migration completed."
        assert projection.response.status.value == "succeeded"


class TestConversationProjection:
    def test_projects_user_turn_and_reply(self) -> None:
        record = _record(
            capability_id="conversation",
            problem="What is the capital of France?",
            explanation="Paris.",
        )
        projection = project_record(record)
        assert isinstance(projection.request, ConversationRequest)
        assert isinstance(projection.response, ConversationResponse)
        assert projection.request.turns[0].content == "What is the capital of France?"
        assert projection.response.reply.content == "Paris."


class TestApprovalProjection:
    def test_projects_subject_and_reason(self) -> None:
        record = _record(
            capability_id="approval",
            problem="Approve deployment to prod?",
            explanation="Looks safe.",
        )
        projection = project_record(record)
        assert isinstance(projection.request, ApprovalRequest)
        assert isinstance(projection.response, ApprovalResponse)
        assert projection.request.subject == "Approve deployment to prod?"
        assert projection.response.reason == "Looks safe."
        assert projection.response.status.value == "approved"

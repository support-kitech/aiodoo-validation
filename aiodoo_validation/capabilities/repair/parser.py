"""RepairRecordParser — native Repair JSON → ParsedCapabilityRecord."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from aiodoo_validation.capabilities.repair.exceptions import RepairParseError
from aiodoo_validation.capabilities.repair.specification import (
    REPAIR_CAPABILITY_ID,
    REPAIR_CORPUS_SCHEMA_ID,
)
from aiodoo_validation.domain.capability_record import (
    CapabilityArtifact,
    ParsedCapabilityRecord,
    TransformationDescriptor,
)
from aiodoo_validation.exceptions import DomainError

_SUPPORTED_SCHEMA_IDS = frozenset(
    {
        REPAIR_CORPUS_SCHEMA_ID,
        "repair-v1",
        "repair_v1",
        "1.0",
        "1.0.0",
    }
)
_REPLACE = "replace"
_MEDIA_BY_TYPE = {
    "python": "text/x-python",
    "xml": "application/xml",
    "manifest": "text/x-python",
    "security": "text/plain",
    "data": "application/octet-stream",
}


def _require_mapping(value: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RepairParseError(f"{label} must be a JSON object.")
    return value


def _require_str(data: Mapping[str, Any], key: str, *, label: str) -> str:
    if key not in data:
        raise RepairParseError(f"{label} missing required field {key!r}.")
    value = data[key]
    if not isinstance(value, str):
        raise RepairParseError(f"{label} field {key!r} must be a string.")
    return value


def _optional_str(data: Mapping[str, Any], key: str, *, label: str) -> str | None:
    if key not in data or data[key] is None:
        return None
    value = data[key]
    if not isinstance(value, str):
        raise RepairParseError(f"{label} field {key!r} must be a string when set.")
    return value


def _check_schema_id(data: Mapping[str, Any]) -> None:
    for key in ("schema_id", "corpus_schema_id"):
        if key in data and data[key] is not None:
            value = data[key]
            if not isinstance(value, str) or value.strip() not in _SUPPORTED_SCHEMA_IDS:
                raise RepairParseError(
                    f"Unsupported Repair schema_id {value!r}; "
                    f"allowed: {sorted(_SUPPORTED_SCHEMA_IDS)}."
                )
    metadata = data.get("metadata")
    if isinstance(metadata, Mapping):
        for key in ("schema_id", "schema_version", "corpus_schema_id"):
            if key in metadata and metadata[key] is not None:
                value = metadata[key]
                if not isinstance(value, str) or value.strip() not in _SUPPORTED_SCHEMA_IDS:
                    raise RepairParseError(
                        f"Unsupported Repair metadata[{key!r}]={value!r}; "
                        f"allowed: {sorted(_SUPPORTED_SCHEMA_IDS)}."
                    )


@dataclass(frozen=True, slots=True)
class RepairRecordParser:
    """
    Convert Repair dataset JSON into generic ``ParsedCapabilityRecord`` values.

    Accepts:
    - A native Repair **task** object (``id`` + ``problem`` + ``context`` + …)
    - A training JSONL **envelope** (``instruction`` / ``output.tasks``)
    - A compact eval fixture shape (``record_id`` / ``artifacts`` / ``operations``)

    Does not build snapshots, apply transforms, or run behavior.
    """

    capability_id: str = REPAIR_CAPABILITY_ID

    def parse(self, data: Mapping[str, Any]) -> ParsedCapabilityRecord:
        """Parse a single task-shaped or compact record."""
        payload = _require_mapping(data, label="Repair record")
        _check_schema_id(payload)
        if self._is_training_envelope(payload):
            records = self.parse_training_example(payload)
            if len(records) != 1:
                raise RepairParseError(
                    "parse() requires exactly one task; "
                    f"training example has {len(records)}. "
                    "Use parse_training_example() for multi-task records."
                )
            return records[0]
        if self._is_compact_record(payload):
            return self._parse_compact(payload)
        return self._parse_task(payload, parent_instruction=None, parent_metadata={})

    def parse_training_example(
        self,
        data: Mapping[str, Any],
    ) -> tuple[ParsedCapabilityRecord, ...]:
        """Expand a training JSONL envelope into one record per task."""
        payload = _require_mapping(data, label="Repair training example")
        _check_schema_id(payload)
        if not self._is_training_envelope(payload):
            raise RepairParseError(
                "Training example must include instruction and output.tasks."
            )
        instruction = _require_str(payload, "instruction", label="Repair training example")
        output = _require_mapping(payload.get("output"), label="output")
        tasks = output.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            raise RepairParseError("output.tasks must be a non-empty list.")
        parent_metadata = payload.get("metadata")
        if parent_metadata is None:
            parent_meta: dict[str, Any] = {}
        else:
            parent_meta = dict(_require_mapping(parent_metadata, label="metadata"))
        records: list[ParsedCapabilityRecord] = []
        for index, task in enumerate(tasks):
            task_map = _require_mapping(task, label=f"output.tasks[{index}]")
            records.append(
                self._parse_task(
                    task_map,
                    parent_instruction=instruction,
                    parent_metadata=parent_meta,
                )
            )
        return tuple(records)

    @staticmethod
    def _is_training_envelope(data: Mapping[str, Any]) -> bool:
        return "output" in data and "instruction" in data

    @staticmethod
    def _is_compact_record(data: Mapping[str, Any]) -> bool:
        return "record_id" in data and "artifacts" in data

    def _parse_compact(self, data: Mapping[str, Any]) -> ParsedCapabilityRecord:
        record_id = _require_str(data, "record_id", label="compact Repair record")
        problem = data.get("problem", "")
        if not isinstance(problem, str):
            raise RepairParseError("compact record field 'problem' must be a string.")
        artifacts_raw = data.get("artifacts")
        if not isinstance(artifacts_raw, list):
            raise RepairParseError("compact record field 'artifacts' must be a list.")
        artifacts = tuple(
            self._artifact_from_mapping(item, index=index, source="compact")
            for index, item in enumerate(artifacts_raw)
        )
        operations = data.get("operations", [])
        if operations is None:
            operations = []
        if not isinstance(operations, list):
            raise RepairParseError("compact record field 'operations' must be a list.")
        transforms = self._operations_to_descriptors(
            operations,
            artifacts=artifacts,
            label="compact operations",
        )
        explanation = _optional_str(data, "explanation", label="compact Repair record")
        tags = self._parse_tags(data.get("tags"))
        metadata = self._merge_metadata(data.get("metadata"), extras={"source": "compact"})
        return self._build_record(
            record_id=record_id,
            problem=problem,
            artifacts=artifacts,
            transformations=transforms,
            explanation=explanation,
            tags=tags,
            metadata=metadata,
        )

    def _parse_task(
        self,
        task: Mapping[str, Any],
        *,
        parent_instruction: str | None,
        parent_metadata: Mapping[str, Any],
    ) -> ParsedCapabilityRecord:
        record_id = _require_str(task, "id", label="Repair task")
        problem_obj = _require_mapping(task.get("problem"), label="problem")
        description = _require_str(problem_obj, "description", label="problem")
        problem_text = description
        if parent_instruction and parent_instruction.strip():
            # Prefer task problem as the behavioral prompt focus; keep instruction
            # in metadata for provenance.
            problem_text = description

        context_raw = task.get("context", [])
        if context_raw is None:
            context_raw = []
        if not isinstance(context_raw, list):
            raise RepairParseError("Repair task field 'context' must be a list.")
        if not context_raw:
            raise RepairParseError(
                f"Repair task {record_id!r} requires at least one context artifact."
            )
        artifacts = tuple(
            self._artifact_from_mapping(item, index=index, source="context")
            for index, item in enumerate(context_raw)
        )

        outcome = _require_mapping(
            task.get("expected_outcome"), label="expected_outcome"
        )
        operations = outcome.get("operations", [])
        if operations is None:
            operations = []
        if not isinstance(operations, list):
            raise RepairParseError("expected_outcome.operations must be a list.")
        transforms = self._operations_to_descriptors(
            operations,
            artifacts=artifacts,
            label=f"task {record_id} operations",
        )
        explanation = _optional_str(outcome, "explanation", label="expected_outcome")

        task_meta = task.get("metadata")
        merged = self._merge_metadata(
            parent_metadata,
            extras={
                "source": "repair_task",
                "severity": problem_obj.get("severity"),
                "location": problem_obj.get("location"),
            },
        )
        if isinstance(task_meta, Mapping):
            merged = {**merged, **dict(task_meta)}
        if parent_instruction:
            merged = {**merged, "instruction": parent_instruction}
        root_cause = task.get("root_cause")
        if isinstance(root_cause, Mapping) and "analysis" in root_cause:
            merged = {**merged, "root_cause": root_cause.get("analysis")}

        tags = self._parse_tags(task.get("tags"))
        constraints = task.get("constraints")
        if isinstance(constraints, list) and constraints:
            merged = {**merged, "constraints": list(constraints)}

        return self._build_record(
            record_id=record_id,
            problem=problem_text,
            artifacts=artifacts,
            transformations=transforms,
            explanation=explanation,
            tags=tags,
            metadata=merged,
        )

    def _artifact_from_mapping(
        self,
        raw: Any,
        *,
        index: int,
        source: str,
    ) -> CapabilityArtifact:
        data = _require_mapping(raw, label=f"{source}[{index}]")
        artifact_id = _require_str(data, "id", label=f"{source}[{index}]")
        path = _require_str(data, "path", label=f"{source}[{index}]")
        if "content" not in data:
            raise RepairParseError(
                f"{source}[{index}] missing required field 'content'."
            )
        content = data["content"]
        if not isinstance(content, str):
            raise RepairParseError(f"{source}[{index}] field 'content' must be a string.")
        type_raw = data.get("type")
        media_type: str | None = None
        meta: dict[str, Any] = {"source": source}
        if isinstance(type_raw, str) and type_raw.strip():
            meta["artifact_type"] = type_raw.strip()
            media_type = _MEDIA_BY_TYPE.get(type_raw.strip())
        for key in ("start_line", "end_line"):
            if key in data and data[key] is not None:
                meta[key] = data[key]
        try:
            return CapabilityArtifact(
                artifact_id=artifact_id,
                path=path,
                content=content,
                media_type=media_type,
                metadata=meta,
            )
        except DomainError as exc:
            raise RepairParseError(str(exc)) from exc

    def _operations_to_descriptors(
        self,
        operations: Sequence[Any],
        *,
        artifacts: Sequence[CapabilityArtifact],
        label: str,
    ) -> tuple[TransformationDescriptor, ...]:
        default_path = self._infer_default_path(artifacts)
        descriptors: list[TransformationDescriptor] = []
        for index, raw in enumerate(operations):
            op = _require_mapping(raw, label=f"{label}[{index}]")
            operation = _require_str(op, "operation", label=f"{label}[{index}]")
            if operation != _REPLACE:
                raise RepairParseError(
                    f"{label}[{index}] has unsupported operation {operation!r}; "
                    f"only {_REPLACE!r} is supported."
                )
            if "search" not in op or "replace" not in op:
                raise RepairParseError(
                    f"{label}[{index}] must include 'search' and 'replace'."
                )
            search = op["search"]
            replace = op["replace"]
            if not isinstance(search, str) or not isinstance(replace, str):
                raise RepairParseError(
                    f"{label}[{index}] fields 'search' and 'replace' must be strings."
                )
            if search == "":
                raise RepairParseError(
                    f"{label}[{index}] field 'search' must be non-empty."
                )
            path = op.get("path")
            if path is None:
                if default_path is None:
                    raise RepairParseError(
                        f"{label}[{index}] missing 'path' and artifact path "
                        "cannot be inferred."
                    )
                path = default_path
            if not isinstance(path, str) or not path.strip():
                raise RepairParseError(
                    f"{label}[{index}] field 'path' must be a non-empty string."
                )
            try:
                descriptors.append(
                    TransformationDescriptor(
                        transformation_type=_REPLACE,
                        payload={
                            "path": path,
                            "search": search,
                            "replace": replace,
                        },
                    )
                )
            except DomainError as exc:
                raise RepairParseError(str(exc)) from exc
        return tuple(descriptors)

    @staticmethod
    def _infer_default_path(artifacts: Sequence[CapabilityArtifact]) -> str | None:
        paths = sorted({item.path for item in artifacts})
        if len(paths) == 1:
            return paths[0]
        return None

    @staticmethod
    def _parse_tags(raw: Any) -> tuple[str, ...]:
        if raw is None:
            return ()
        if not isinstance(raw, list):
            raise RepairParseError("tags must be a list of strings when set.")
        tags = tuple(str(item) for item in raw)
        return tags

    @staticmethod
    def _merge_metadata(
        raw: Any,
        *,
        extras: Mapping[str, Any],
    ) -> dict[str, Any]:
        base: dict[str, Any] = {}
        if raw is None:
            pass
        elif isinstance(raw, Mapping):
            base.update(dict(raw))
        else:
            raise RepairParseError("metadata must be a JSON object when set.")
        for key, value in extras.items():
            if value is not None:
                base[key] = value
        return base

    def _build_record(
        self,
        *,
        record_id: str,
        problem: str,
        artifacts: tuple[CapabilityArtifact, ...],
        transformations: tuple[TransformationDescriptor, ...],
        explanation: str | None,
        tags: tuple[str, ...],
        metadata: Mapping[str, Any],
    ) -> ParsedCapabilityRecord:
        try:
            return ParsedCapabilityRecord(
                record_id=record_id,
                capability_id=self.capability_id,
                problem=problem,
                artifacts=artifacts,
                transformations=transformations,
                explanation=explanation,
                tags=tags,
                metadata=dict(metadata),
            )
        except DomainError as exc:
            raise RepairParseError(str(exc)) from exc


__all__ = ["RepairRecordParser"]

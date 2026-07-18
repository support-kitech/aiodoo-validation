"""Generic BehaviorCaseBuilder (Capability Delivery E3).

Assembles ``ParsedCapabilityRecord`` → ``BehaviorCase`` (+ snapshots / mapped
replace transforms). Does not load corpora, parse Repair schemas, execute
transforms, run behavior, score, or certify.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from aiodoo_validation.behavior.build_result import BehaviorCaseBuildResult
from aiodoo_validation.behavior.exceptions import BehaviorCaseBuildError
from aiodoo_validation.domain.behavior import (
    BehaviorCase,
    BehaviorPrompt,
    ExpectedOutput,
)
from aiodoo_validation.domain.capability_record import (
    CapabilityArtifact,
    ParsedCapabilityRecord,
    TransformationDescriptor,
)
from aiodoo_validation.domain.capability_spec import CapabilitySpecification
from aiodoo_validation.domain.enums import ComparatorKind
from aiodoo_validation.transforms.exceptions import TransformationValidationError
from aiodoo_validation.transforms.replace import ReplaceTransformation
from aiodoo_validation.transforms.snapshot import ArtifactSnapshot

_SNAPSHOT_ROLE_KEY = "snapshot_role"
_ROLE_ORIGINAL = "original"
_ROLE_EXPECTED = "expected"
_REPLACE_TYPE = "replace"


def _artifact_role(artifact: CapabilityArtifact) -> str:
    raw = artifact.metadata.get(_SNAPSHOT_ROLE_KEY, _ROLE_ORIGINAL)
    if not isinstance(raw, str) or not raw.strip():
        raise BehaviorCaseBuildError(
            f"Artifact {artifact.artifact_id!r} has invalid "
            f"metadata[{_SNAPSHOT_ROLE_KEY!r}]."
        )
    role = raw.strip()
    if role not in {_ROLE_ORIGINAL, _ROLE_EXPECTED}:
        raise BehaviorCaseBuildError(
            f"Artifact {artifact.artifact_id!r} has unsupported "
            f"snapshot_role {role!r}; allowed: "
            f"{_ROLE_ORIGINAL!r}, {_ROLE_EXPECTED!r}."
        )
    return role


def _contents_from_artifacts(
    artifacts: Sequence[CapabilityArtifact],
    *,
    role: str,
) -> dict[str, str]:
    contents: dict[str, str] = {}
    for artifact in artifacts:
        if _artifact_role(artifact) != role:
            continue
        if artifact.path in contents:
            raise BehaviorCaseBuildError(
                f"Duplicate artifact path {artifact.path!r} for snapshot_role {role!r}."
            )
        contents[artifact.path] = artifact.content
    return contents


def _resolve_comparator_kind(
    specification: CapabilitySpecification,
    record: ParsedCapabilityRecord,
) -> ComparatorKind:
    override = record.metadata.get("comparator_kind")
    if override is not None:
        if not isinstance(override, str) or not override.strip():
            raise BehaviorCaseBuildError(
                "Record metadata 'comparator_kind' must be a non-empty string."
            )
        kind_value = override.strip()
    else:
        kind_value = specification.supported_comparator_kinds[0]

    try:
        kind = ComparatorKind(kind_value)
    except ValueError as exc:
        raise BehaviorCaseBuildError(
            f"Unsupported comparator_kind {kind_value!r}."
        ) from exc

    if kind.value not in specification.supported_comparator_kinds:
        raise BehaviorCaseBuildError(
            f"Comparator kind {kind.value!r} is not declared in Capability "
            f"Specification {specification.id!r}."
        )
    return kind


def descriptor_to_replace_transformation(
    descriptor: TransformationDescriptor,
) -> ReplaceTransformation:
    """
    Map a generic ``TransformationDescriptor`` to ``ReplaceTransformation``.

    Only ``transformation_type == "replace"`` is supported in Spec v1.0.
    Payload keys: ``path``, ``search``, ``replace`` (all strings).
    """
    if descriptor.transformation_type != _REPLACE_TYPE:
        raise BehaviorCaseBuildError(
            f"Unsupported transformation_type {descriptor.transformation_type!r}; "
            f"only {_REPLACE_TYPE!r} is supported."
        )
    payload = descriptor.payload
    for key in ("path", "search", "replace"):
        if key not in payload:
            raise BehaviorCaseBuildError(
                f"Replace transformation payload missing required field {key!r}."
            )
        if not isinstance(payload[key], str):
            raise BehaviorCaseBuildError(
                f"Replace transformation payload field {key!r} must be a string."
            )
    try:
        return ReplaceTransformation(
            path=payload["path"],
            search=payload["search"],
            replace=payload["replace"],
            metadata={"transformation_type": _REPLACE_TYPE},
        )
    except TransformationValidationError as exc:
        raise BehaviorCaseBuildError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class BehaviorCaseBuilder:
    """
    Assemble executable behavior cases from normalized capability records.

    One ``ParsedCapabilityRecord`` yields one ``BehaviorCaseBuildResult``.
    Does not execute transformations or invoke BehaviorRunner.
    """

    def build(
        self,
        record: ParsedCapabilityRecord,
        specification: CapabilitySpecification,
    ) -> BehaviorCaseBuildResult:
        if not isinstance(record, ParsedCapabilityRecord):
            raise TypeError("record must be a ParsedCapabilityRecord.")
        if not isinstance(specification, CapabilitySpecification):
            raise TypeError("specification must be a CapabilitySpecification.")

        if record.capability_id != specification.id:
            raise BehaviorCaseBuildError(
                f"Record capability_id {record.capability_id!r} does not match "
                f"Capability Specification id {specification.id!r}."
            )

        if not record.artifacts and not record.problem.strip():
            raise BehaviorCaseBuildError(
                f"Record {record.record_id!r} requires a non-empty problem "
                "and/or at least one artifact."
            )

        original_contents = _contents_from_artifacts(
            record.artifacts, role=_ROLE_ORIGINAL
        )
        expected_contents = _contents_from_artifacts(
            record.artifacts, role=_ROLE_EXPECTED
        )

        # Expected artifacts are optional. When absent, expected starts as a
        # copy of original content — gold may be expressed as transformations
        # applied later (not here).
        if not expected_contents:
            expected_contents = dict(original_contents)

        if record.transformations and not original_contents:
            raise BehaviorCaseBuildError(
                f"Record {record.record_id!r} declares transformations but has "
                "no original artifacts."
            )

        original_snapshot = ArtifactSnapshot(
            snapshot_id=f"{record.record_id}.original",
            contents=original_contents,
            metadata={"record_id": record.record_id, "role": _ROLE_ORIGINAL},
        )
        expected_snapshot = ArtifactSnapshot(
            snapshot_id=f"{record.record_id}.expected",
            contents=expected_contents,
            metadata={"record_id": record.record_id, "role": _ROLE_EXPECTED},
        )

        mapped: list[ReplaceTransformation] = []
        for index, descriptor in enumerate(record.transformations):
            if (
                descriptor.transformation_type
                not in specification.supported_transformation_types
            ):
                raise BehaviorCaseBuildError(
                    f"Transformation type {descriptor.transformation_type!r} "
                    f"at index {index} is not declared in Capability "
                    f"Specification {specification.id!r}."
                )
            transform = descriptor_to_replace_transformation(descriptor)
            if transform.path not in original_snapshot.contents:
                raise BehaviorCaseBuildError(
                    f"Transformation at index {index} references path "
                    f"{transform.path!r} which is absent from the original snapshot."
                )
            mapped.append(transform)

        comparator_kind = _resolve_comparator_kind(specification, record)
        expected_text = self._expected_text(record, expected_snapshot)
        case_metadata: dict[str, Any] = {
            "capability_id": record.capability_id,
            "record_id": record.record_id,
            "original_snapshot_id": original_snapshot.snapshot_id,
            "expected_snapshot_id": expected_snapshot.snapshot_id,
            "transformation_count": len(mapped),
            "artifact_count": len(record.artifacts),
        }
        if record.explanation is not None:
            case_metadata["explanation"] = record.explanation
        case_metadata.update(
            {
                key: value
                for key, value in dict(record.metadata).items()
                if key != "comparator_kind"
            }
        )

        case = BehaviorCase(
            case_id=record.record_id,
            prompt=BehaviorPrompt(
                text=record.problem,
                metadata=MappingProxyType(
                    {
                        "capability_id": record.capability_id,
                        "record_id": record.record_id,
                    }
                ),
            ),
            expected=ExpectedOutput(
                text=expected_text,
                metadata=MappingProxyType(
                    {
                        "source": (
                            "expected_artifacts"
                            if any(
                                _artifact_role(item) == _ROLE_EXPECTED
                                for item in record.artifacts
                            )
                            else "original_copy"
                        )
                    }
                ),
            ),
            comparator_kind=comparator_kind,
            tags=record.tags,
            metadata=MappingProxyType(case_metadata),
        )

        return BehaviorCaseBuildResult(
            case=case,
            original_snapshot=original_snapshot,
            expected_snapshot=expected_snapshot,
            transformations=tuple(mapped),
            record_id=record.record_id,
            capability_id=record.capability_id,
            metadata=MappingProxyType(
                {
                    "specification_id": specification.id,
                    "specification_version": specification.version,
                }
            ),
        )

    def build_many(
        self,
        records: Sequence[ParsedCapabilityRecord],
        specification: CapabilitySpecification,
    ) -> tuple[BehaviorCaseBuildResult, ...]:
        return tuple(self.build(record, specification) for record in records)

    @staticmethod
    def _expected_text(
        record: ParsedCapabilityRecord,
        expected_snapshot: ArtifactSnapshot,
    ) -> str:
        """
        Text expected by BehaviorRunner-style exact comparison.

        Prefer explicit expected-role artifact contents (stable path order).
        Fall back to explanation, then empty string for transform-only gold.
        """
        expected_artifacts = [
            item
            for item in record.artifacts
            if _artifact_role(item) == _ROLE_EXPECTED
        ]
        if expected_artifacts:
            parts = [
                expected_snapshot.require(item.path) for item in expected_artifacts
            ]
            return "\n".join(parts)
        if record.explanation is not None:
            return record.explanation
        return ""


__all__ = [
    "BehaviorCaseBuilder",
    "descriptor_to_replace_transformation",
]

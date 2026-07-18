"""Capability Specification domain types (declarative metadata only)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import CorpusRole, ValidationKind
from aiodoo_validation.exceptions import DomainError


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, Mapping):
        raise DomainError("mapping field must be a mapping.")
    return MappingProxyType(dict(value))


def _normalize_str_tuple(
    values: Sequence[str] | None,
    *,
    field_name: str,
    allow_empty: bool,
) -> tuple[str, ...]:
    if values is None:
        items: tuple[str, ...] = ()
    else:
        items = tuple(str(item).strip() for item in values)
        if any(not item for item in items):
            raise DomainError(f"{field_name} entries must be non-empty strings.")
        if len(items) != len(set(items)):
            raise DomainError(f"{field_name} must not contain duplicates.")
    if not allow_empty and not items:
        raise DomainError(f"{field_name} must contain at least one entry.")
    return items


@dataclass(frozen=True, slots=True)
class CorpusRequirements:
    """Corpus constraints declared by a Capability Specification."""

    role: CorpusRole
    fingerprint_required: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.role, CorpusRole):
            raise DomainError(f"role must be CorpusRole, got {type(self.role)!r}.")
        # Spec v1.0: production capability specs require evaluation + fingerprint.
        if self.role is not CorpusRole.EVALUATION:
            raise DomainError(
                "Capability Specification corpus_requirements.role must be "
                f"{CorpusRole.EVALUATION.value!r}."
            )
        if not self.fingerprint_required:
            raise DomainError(
                "Capability Specification corpus_requirements.fingerprint_required "
                "must be True."
            )


@dataclass(frozen=True, slots=True)
class RuntimeRequirements:
    """Runtime constraints declared by a Capability Specification."""

    behavior_certification: str
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.behavior_certification.strip():
            raise DomainError("behavior_certification must be non-empty.")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class CapabilitySpecification:
    """
    Declarative capability metadata (Spec v1.0).

    No parsers, callbacks, loaders, or DI — string refs only (``parser_id``,
    policy refs).
    """

    id: str
    name: str
    description: str
    version: str
    supported_artifact_types: tuple[str, ...]
    supported_transformation_types: tuple[str, ...]
    supported_comparator_kinds: tuple[str, ...]
    supported_evaluation_dimensions: tuple[str, ...]
    supported_certification_kinds: tuple[str, ...]
    corpus_schema_id: str
    corpus_requirements: CorpusRequirements
    default_scoring_policy_ref: str
    default_certification_policy_ref: str
    runtime_requirements: RuntimeRequirements
    parser_id: str
    supported_languages: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        for field_name in (
            "id",
            "name",
            "description",
            "version",
            "corpus_schema_id",
            "default_scoring_policy_ref",
            "default_certification_policy_ref",
            "parser_id",
        ):
            value = getattr(self, field_name)
            if not str(value).strip():
                raise DomainError(f"{field_name} must be non-empty.")

        if not isinstance(self.corpus_requirements, CorpusRequirements):
            raise DomainError("corpus_requirements must be CorpusRequirements.")
        if not isinstance(self.runtime_requirements, RuntimeRequirements):
            raise DomainError("runtime_requirements must be RuntimeRequirements.")

        object.__setattr__(
            self,
            "supported_artifact_types",
            _normalize_str_tuple(
                self.supported_artifact_types,
                field_name="supported_artifact_types",
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "supported_transformation_types",
            _normalize_str_tuple(
                self.supported_transformation_types,
                field_name="supported_transformation_types",
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "supported_comparator_kinds",
            _normalize_str_tuple(
                self.supported_comparator_kinds,
                field_name="supported_comparator_kinds",
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "supported_evaluation_dimensions",
            _normalize_str_tuple(
                self.supported_evaluation_dimensions,
                field_name="supported_evaluation_dimensions",
                allow_empty=False,
            ),
        )
        kinds = _normalize_str_tuple(
            self.supported_certification_kinds,
            field_name="supported_certification_kinds",
            allow_empty=False,
        )
        allowed_kinds = {member.value for member in ValidationKind}
        unknown = sorted(set(kinds) - allowed_kinds)
        if unknown:
            raise DomainError(
                "supported_certification_kinds contains unknown values "
                f"{unknown}; allowed: {sorted(allowed_kinds)}."
            )
        object.__setattr__(self, "supported_certification_kinds", kinds)
        object.__setattr__(
            self,
            "supported_languages",
            _normalize_str_tuple(
                self.supported_languages,
                field_name="supported_languages",
                allow_empty=True,
            ),
        )
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


__all__ = [
    "CapabilitySpecification",
    "CorpusRequirements",
    "RuntimeRequirements",
]

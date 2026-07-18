"""Corpus metadata domain types (Capability Delivery).

Metadata only — no filesystem I/O, loading, or gate evaluation.
Gate logic belongs in the corpus package (E1).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import CorpusRole
from aiodoo_validation.exceptions import DomainError


def _as_frozen_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, Mapping):
        raise DomainError("metadata must be a mapping.")
    return MappingProxyType(dict(value))


def _as_frozen_str_tuple(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    return tuple(str(item) for item in values)


@dataclass(frozen=True, slots=True)
class CorpusManifest:
    """
    Immutable corpus metadata (Spec v1.0).

    ``capability_id`` is the same identity as ``CapabilitySpecification.id`` and
    the validation profile name (``ValidationRequest.profile_name`` / CLI
    ``--profile``). Do not invent a second identifier.

    Does not load records or enforce train/eval policy — that is E1 gate logic.
    """

    corpus_id: str
    capability_id: str
    role: CorpusRole
    dataset_version: str
    fingerprint: str
    source_package: str | None = None
    denied_training_fingerprints: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.corpus_id.strip():
            raise DomainError("corpus_id must be non-empty.")
        if not self.capability_id.strip():
            raise DomainError("capability_id must be non-empty.")
        if not isinstance(self.role, CorpusRole):
            raise DomainError(f"role must be CorpusRole, got {type(self.role)!r}.")
        if not self.dataset_version.strip():
            raise DomainError("dataset_version must be non-empty.")
        if not self.fingerprint.strip():
            raise DomainError("fingerprint must be non-empty.")
        if self.source_package is not None and not self.source_package.strip():
            raise DomainError("source_package must be non-empty when provided.")

        denied = _as_frozen_str_tuple(self.denied_training_fingerprints)
        if len(denied) != len(set(denied)):
            raise DomainError("denied_training_fingerprints must not contain duplicates.")
        object.__setattr__(self, "denied_training_fingerprints", denied)
        object.__setattr__(self, "metadata", _as_frozen_mapping(self.metadata))


__all__ = ["CorpusManifest"]

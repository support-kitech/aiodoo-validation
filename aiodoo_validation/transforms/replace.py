"""Replace-only transformation descriptor (first Spec transform type)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.transforms.exceptions import TransformationValidationError


@dataclass(frozen=True, slots=True)
class ReplaceTransformation:
    """
    Literal search/replace on one snapshot path.

    No regex. No flags. No multi-op language. Empty ``search`` is rejected.
    Empty ``replace`` is allowed (delete matched text).
    """

    path: str
    search: str
    replace: str
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path.strip():
            raise TransformationValidationError("path must be a non-empty string.")
        if not isinstance(self.search, str):
            raise TransformationValidationError("search must be a string.")
        if self.search == "":
            raise TransformationValidationError("search must be non-empty.")
        if not isinstance(self.replace, str):
            raise TransformationValidationError("replace must be a string.")
        if self.metadata is None:
            object.__setattr__(self, "metadata", MappingProxyType({}))
        elif not isinstance(self.metadata, Mapping):
            raise TransformationValidationError("metadata must be a mapping.")
        else:
            object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


__all__ = ["ReplaceTransformation"]

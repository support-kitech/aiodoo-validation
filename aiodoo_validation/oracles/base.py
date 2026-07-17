"""Oracle protocol interface."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.oracle import OracleContext, OracleMetadata, OracleResult


class Oracle(Protocol):
    """
    Contract for a validation oracle.

    Oracles expose immutable metadata and return immutable OracleResult values.
    """

    @property
    def metadata(self) -> OracleMetadata: ...

    def execute(self, context: OracleContext) -> OracleResult: ...

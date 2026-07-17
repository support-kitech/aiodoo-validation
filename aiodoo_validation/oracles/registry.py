"""Oracle registry (Phase 5)."""

from __future__ import annotations

from dataclasses import dataclass, field

from aiodoo_validation.domain.enums import OracleErrorCode
from aiodoo_validation.domain.oracle import OracleError
from aiodoo_validation.oracles.base import Oracle
from aiodoo_validation.oracles.placeholders import default_coding_placeholder_oracles


@dataclass
class OracleRegistry:
    """
    Register and resolve oracle implementations by ID.

    Supports future plugins and additional profiles without engine changes.
    """

    _oracles: dict[str, Oracle] = field(default_factory=dict)

    @classmethod
    def create_default(cls) -> OracleRegistry:
        registry = cls()
        for oracle in default_coding_placeholder_oracles():
            registry.register(oracle)
        return registry

    def register(self, oracle: Oracle) -> None:
        oracle_id = oracle.metadata.oracle_id
        if not oracle_id:
            raise OracleError(
                code=OracleErrorCode.REGISTRATION_FAILURE,
                message="Oracle metadata must include a non-empty oracle_id.",
                field="oracle_id",
            )
        if oracle_id in self._oracles:
            raise OracleError(
                code=OracleErrorCode.REGISTRATION_FAILURE,
                message=f"Oracle {oracle_id!r} is already registered.",
                field="oracle_id",
                oracle_id=oracle_id,
            )
        self._oracles[oracle_id] = oracle

    def get(self, oracle_id: str) -> Oracle:
        oracle = self._oracles.get(oracle_id)
        if oracle is None:
            raise OracleError(
                code=OracleErrorCode.ORACLE_NOT_FOUND,
                message=f"Oracle {oracle_id!r} is not registered.",
                field="oracle_id",
                oracle_id=oracle_id,
            )
        return oracle

    def resolve(self, oracle_id: str) -> Oracle | None:
        return self._oracles.get(oracle_id)

    def contains(self, oracle_id: str) -> bool:
        return oracle_id in self._oracles

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._oracles))

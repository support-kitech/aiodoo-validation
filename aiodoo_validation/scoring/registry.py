"""Scoring policy registry (Phase 6)."""

from __future__ import annotations

from dataclasses import dataclass, field

from aiodoo_validation.domain.enums import ScoreErrorCode
from aiodoo_validation.domain.scoring import ScoreError
from aiodoo_validation.scoring.base import ScorePolicy
from aiodoo_validation.scoring.policies import default_coding_placeholder_policies


@dataclass
class ScoringRegistry:
    """
    Register and resolve scoring policies by ID.

    Supports future plugins and additional profiles without engine changes.
    """

    _policies: dict[str, ScorePolicy] = field(default_factory=dict)

    @classmethod
    def create_default(cls) -> ScoringRegistry:
        registry = cls()
        for policy in default_coding_placeholder_policies():
            registry.register(policy)
        return registry

    def register(self, policy: ScorePolicy) -> None:
        policy_id = policy.metadata.policy_id
        if not policy_id:
            raise ScoreError(
                code=ScoreErrorCode.REGISTRATION_FAILURE,
                message="Score policy metadata must include a non-empty policy_id.",
                field="policy_id",
            )
        if policy_id in self._policies:
            raise ScoreError(
                code=ScoreErrorCode.REGISTRATION_FAILURE,
                message=f"Score policy {policy_id!r} is already registered.",
                field="policy_id",
                policy_id=policy_id,
            )
        self._policies[policy_id] = policy

    def get(self, policy_id: str) -> ScorePolicy:
        policy = self._policies.get(policy_id)
        if policy is None:
            raise ScoreError(
                code=ScoreErrorCode.POLICY_NOT_FOUND,
                message=f"Score policy {policy_id!r} is not registered.",
                field="policy_id",
                policy_id=policy_id,
            )
        return policy

    def resolve(self, policy_id: str) -> ScorePolicy | None:
        return self._policies.get(policy_id)

    def contains(self, policy_id: str) -> bool:
        return policy_id in self._policies

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._policies))

"""Benchmark policy registry (Phase 7)."""

from __future__ import annotations

from dataclasses import dataclass, field

from aiodoo_validation.benchmark.base import BenchmarkPolicy
from aiodoo_validation.benchmark.policies import default_coding_placeholder_policies
from aiodoo_validation.domain.benchmark import BenchmarkError
from aiodoo_validation.domain.enums import BenchmarkErrorCode


@dataclass
class BenchmarkRegistry:
    """
    Register and resolve benchmark policies by ID.

    Supports future plugins and additional profiles without engine changes.
    """

    _policies: dict[str, BenchmarkPolicy] = field(default_factory=dict)

    @classmethod
    def create_default(cls) -> BenchmarkRegistry:
        registry = cls()
        for policy in default_coding_placeholder_policies():
            registry.register(policy)
        return registry

    def register(self, policy: BenchmarkPolicy) -> None:
        policy_id = policy.metadata.policy_id
        if not policy_id:
            raise BenchmarkError(
                code=BenchmarkErrorCode.REGISTRATION_FAILURE,
                message="Benchmark policy metadata must include a non-empty policy_id.",
                field="policy_id",
            )
        if policy_id in self._policies:
            raise BenchmarkError(
                code=BenchmarkErrorCode.REGISTRATION_FAILURE,
                message=f"Benchmark policy {policy_id!r} is already registered.",
                field="policy_id",
                policy_id=policy_id,
            )
        self._policies[policy_id] = policy

    def get(self, policy_id: str) -> BenchmarkPolicy:
        policy = self._policies.get(policy_id)
        if policy is None:
            raise BenchmarkError(
                code=BenchmarkErrorCode.POLICY_NOT_FOUND,
                message=f"Benchmark policy {policy_id!r} is not registered.",
                field="policy_id",
                policy_id=policy_id,
            )
        return policy

    def resolve(self, policy_id: str) -> BenchmarkPolicy | None:
        return self._policies.get(policy_id)

    def contains(self, policy_id: str) -> bool:
        return policy_id in self._policies

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._policies))

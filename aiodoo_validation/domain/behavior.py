"""Behavioral validation domain types.

Flow (architecture):
    BehaviorCase.prompt → Inference → GeneratedOutput
        ↘ ExpectedOutput → Comparator → BehaviorResult → Scoring hooks
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import ComparatorKind, ValidationKind


@dataclass(frozen=True, slots=True)
class BehaviorPrompt:
    """Prompt material for a single behavioral evaluation case."""

    text: str
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class ExpectedOutput:
    """Expected model output for a behavioral case."""

    text: str
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class GeneratedOutput:
    """Model-generated output captured during behavioral evaluation."""

    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: int | None = None
    memory_usage_mb: float | None = None
    runtime: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class BehaviorCase:
    """One prompt/expected pair for behavioral validation."""

    case_id: str
    prompt: BehaviorPrompt
    expected: ExpectedOutput
    comparator_kind: ComparatorKind = ComparatorKind.EXACT
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class BehaviorResult:
    """Immutable result for a single behavioral case."""

    case_id: str
    passed: bool
    message: str
    comparator_kind: ComparatorKind
    similarity: float | None = None
    generated: GeneratedOutput | None = None
    expected: ExpectedOutput | None = None
    findings: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    duration_ms: int = 0
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    @property
    def validation_kind(self) -> ValidationKind:
        return ValidationKind.BEHAVIORAL


@dataclass(frozen=True, slots=True)
class BehaviorSuiteResult:
    """Aggregate result of running a behavioral case suite."""

    suite_id: str
    profile_name: str
    results: tuple[BehaviorResult, ...]
    duration_ms: int
    case_count: int
    pass_count: int
    fail_count: int
    deferred: bool = False
    deferred_reason: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    @property
    def all_passed(self) -> bool:
        return not self.deferred and self.case_count > 0 and self.fail_count == 0


@dataclass(frozen=True, slots=True)
class BehaviorCorpus:
    """
    Immutable behavioral evaluation corpus.

    Production corpora are supplied by external dataset packages. An empty
    corpus means behavioral evaluation is deferred — never invent cases.
    """

    corpus_id: str
    profile_name: str
    cases: tuple[BehaviorCase, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    @property
    def is_empty(self) -> bool:
        return len(self.cases) == 0

    def limited(self, limit: int | None) -> BehaviorCorpus:
        """Return a corpus capped to ``limit`` cases (``None`` = no cap)."""
        if limit is None:
            return self
        if limit <= 0:
            return BehaviorCorpus(
                corpus_id=self.corpus_id,
                profile_name=self.profile_name,
                cases=(),
                metadata=MappingProxyType(
                    {**dict(self.metadata), "limit_applied": 0}
                ),
            )
        if len(self.cases) <= limit:
            return self
        return BehaviorCorpus(
            corpus_id=self.corpus_id,
            profile_name=self.profile_name,
            cases=self.cases[:limit],
            metadata=MappingProxyType(
                {**dict(self.metadata), "limit_applied": limit}
            ),
        )


def empty_behavior_corpus(*, profile_name: str, corpus_id: str | None = None) -> BehaviorCorpus:
    """Factory for an intentionally empty corpus (deferred behavioral eval)."""
    return BehaviorCorpus(
        corpus_id=corpus_id or f"{profile_name}.behavior.empty",
        profile_name=profile_name,
        cases=(),
        metadata=MappingProxyType({"deferred": True}),
    )


def select_cases(
    cases: Sequence[BehaviorCase],
    *,
    limit: int | None,
) -> tuple[BehaviorCase, ...]:
    """Apply a smoke/full case limit without inventing data."""
    if limit is None:
        return tuple(cases)
    if limit <= 0:
        return ()
    return tuple(cases[:limit])


__all__ = [
    "BehaviorCase",
    "BehaviorCorpus",
    "BehaviorPrompt",
    "BehaviorResult",
    "BehaviorSuiteResult",
    "ExpectedOutput",
    "GeneratedOutput",
    "empty_behavior_corpus",
    "select_cases",
]

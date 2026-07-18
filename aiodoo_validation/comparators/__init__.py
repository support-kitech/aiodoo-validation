"""Comparator protocol and registry for behavioral validation."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.comparators.structural import (
    AstComparator,
    JsonComparator,
    TokenSimilarityComparator,
    XmlComparator,
)
from aiodoo_validation.domain.behavior import ExpectedOutput, GeneratedOutput
from aiodoo_validation.domain.comparator import (
    ComparatorCapability,
    ComparatorMetadata,
    ComparatorResult,
)
from aiodoo_validation.domain.enums import ComparatorKind


class Comparator(Protocol):
    """Compare expected vs generated output."""

    @property
    def metadata(self) -> ComparatorMetadata: ...

    def compare(
        self,
        *,
        expected: ExpectedOutput,
        generated: GeneratedOutput,
    ) -> ComparatorResult: ...


class DeferredComparator:
    """Architecture stub for comparators that require AI or domain rule packs."""

    def __init__(self, metadata: ComparatorMetadata) -> None:
        self._metadata = metadata

    @property
    def metadata(self) -> ComparatorMetadata:
        return self._metadata

    def compare(
        self,
        *,
        expected: ExpectedOutput,
        generated: GeneratedOutput,
    ) -> ComparatorResult:
        _ = expected, generated
        return ComparatorResult(
            passed=False,
            similarity=None,
            message=(
                f"Comparator {self._metadata.kind.value!r} is not implemented yet "
                "(requires AI or domain rule packs)."
            ),
            findings=("deferred_comparator",),
            metadata={"implemented": False, "kind": self._metadata.kind.value},
        )


class ExactMatchComparator:
    """Pass when generated text exactly equals expected text."""

    def __init__(self) -> None:
        self._metadata = ComparatorMetadata(
            comparator_id="comparator.exact",
            kind=ComparatorKind.EXACT,
            name="Exact Match",
            description="Byte-for-byte equality of generated and expected text.",
            version="1.0.0",
            capabilities=ComparatorCapability(implemented=True),
        )

    @property
    def metadata(self) -> ComparatorMetadata:
        return self._metadata

    def compare(
        self,
        *,
        expected: ExpectedOutput,
        generated: GeneratedOutput,
    ) -> ComparatorResult:
        passed = generated.text == expected.text
        return ComparatorResult(
            passed=passed,
            similarity=1.0 if passed else 0.0,
            message="Exact match." if passed else "Exact match failed.",
            findings=("exact_match",) if passed else ("exact_mismatch",),
            metadata={"implemented": True, "kind": ComparatorKind.EXACT.value},
        )


class NormalizedTextComparator:
    """Pass when stripped/collapsed whitespace forms match (case-sensitive)."""

    def __init__(self) -> None:
        self._metadata = ComparatorMetadata(
            comparator_id="comparator.normalized_text",
            kind=ComparatorKind.NORMALIZED_TEXT,
            name="Normalized Text",
            description="Compare after stripping and collapsing whitespace.",
            version="1.0.0",
            capabilities=ComparatorCapability(implemented=True),
        )

    @property
    def metadata(self) -> ComparatorMetadata:
        return self._metadata

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.split())

    def compare(
        self,
        *,
        expected: ExpectedOutput,
        generated: GeneratedOutput,
    ) -> ComparatorResult:
        left = self._normalize(expected.text)
        right = self._normalize(generated.text)
        passed = left == right
        return ComparatorResult(
            passed=passed,
            similarity=1.0 if passed else 0.0,
            message="Normalized text match." if passed else "Normalized text mismatch.",
            findings=("normalized_match",) if passed else ("normalized_mismatch",),
            metadata={"implemented": True, "kind": ComparatorKind.NORMALIZED_TEXT.value},
        )


def deferred_comparator(kind: ComparatorKind, *, name: str, description: str) -> DeferredComparator:
    return DeferredComparator(
        ComparatorMetadata(
            comparator_id=f"comparator.{kind.value}",
            kind=kind,
            name=name,
            description=description,
            version="0.0.0-architecture",
            capabilities=ComparatorCapability(
                implemented=False,
                requires_model=kind is ComparatorKind.SEMANTIC,
            ),
        )
    )


class ComparatorRegistry:
    """Lookup comparators by ``ComparatorKind``."""

    def __init__(self) -> None:
        self._by_kind: dict[ComparatorKind, Comparator] = {}

    def register(self, comparator: Comparator) -> None:
        self._by_kind[comparator.metadata.kind] = comparator

    def get(self, kind: ComparatorKind) -> Comparator:
        if kind not in self._by_kind:
            raise KeyError(f"No comparator registered for {kind.value!r}.")
        return self._by_kind[kind]

    def get_optional(self, kind: ComparatorKind) -> Comparator | None:
        return self._by_kind.get(kind)

    @classmethod
    def create_default(cls) -> ComparatorRegistry:
        registry = cls()
        registry.register(ExactMatchComparator())
        registry.register(NormalizedTextComparator())
        registry.register(AstComparator())
        registry.register(XmlComparator())
        registry.register(JsonComparator())
        registry.register(TokenSimilarityComparator())
        registry.register(
            deferred_comparator(
                ComparatorKind.SEMANTIC,
                name="Semantic Comparison",
                description="Model-based semantic similarity (intentionally deferred).",
            )
        )
        registry.register(
            deferred_comparator(
                ComparatorKind.RULE_BASED,
                name="Rule Based Comparison",
                description="Domain rule packs (intentionally deferred).",
            )
        )
        return registry


__all__ = [
    "AstComparator",
    "Comparator",
    "ComparatorRegistry",
    "DeferredComparator",
    "ExactMatchComparator",
    "JsonComparator",
    "NormalizedTextComparator",
    "TokenSimilarityComparator",
    "XmlComparator",
    "deferred_comparator",
]

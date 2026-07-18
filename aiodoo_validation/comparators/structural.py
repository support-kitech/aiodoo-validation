"""Deterministic structural comparators (no AI / no semantic models)."""

from __future__ import annotations

import ast
import json
import xml.etree.ElementTree as ET
from collections import Counter

from aiodoo_validation.domain.behavior import ExpectedOutput, GeneratedOutput
from aiodoo_validation.domain.comparator import (
    ComparatorCapability,
    ComparatorMetadata,
    ComparatorResult,
)
from aiodoo_validation.domain.enums import ComparatorKind


class AstComparator:
    """Compare Python source via AST dump equality (ignores formatting)."""

    def __init__(self) -> None:
        self._metadata = ComparatorMetadata(
            comparator_id="comparator.ast",
            kind=ComparatorKind.AST,
            name="AST Comparison",
            description="Compare Python AST structure after parsing.",
            version="1.0.0",
            capabilities=ComparatorCapability(
                implemented=True,
                requires_ast=True,
                requires_python=True,
                supports_cpu=True,
                deterministic=True,
                behavioral_only=True,
            ),
        )

    @property
    def metadata(self) -> ComparatorMetadata:
        return self._metadata

    @staticmethod
    def _dump(source: str) -> str:
        tree = ast.parse(source)
        return ast.dump(tree, annotate_fields=True, include_attributes=False)

    def compare(
        self,
        *,
        expected: ExpectedOutput,
        generated: GeneratedOutput,
    ) -> ComparatorResult:
        try:
            left = self._dump(expected.text)
            right = self._dump(generated.text)
        except SyntaxError as exc:
            return ComparatorResult(
                passed=False,
                similarity=None,
                message=f"AST parse failed: {exc.msg}",
                findings=("ast_parse_error",),
                metadata={
                    "implemented": True,
                    "kind": ComparatorKind.AST.value,
                    "error": str(exc),
                },
            )
        passed = left == right
        return ComparatorResult(
            passed=passed,
            similarity=1.0 if passed else 0.0,
            message="AST match." if passed else "AST mismatch.",
            findings=("ast_match",) if passed else ("ast_mismatch",),
            metadata={"implemented": True, "kind": ComparatorKind.AST.value},
        )


class XmlComparator:
    """Compare XML via canonical tree serialization (attribute-order independent)."""

    def __init__(self) -> None:
        self._metadata = ComparatorMetadata(
            comparator_id="comparator.xml",
            kind=ComparatorKind.XML,
            name="XML Comparison",
            description="Compare XML trees after canonicalization.",
            version="1.0.0",
            capabilities=ComparatorCapability(
                implemented=True,
                requires_xml=True,
                requires_xml_parser=True,
                supports_cpu=True,
                deterministic=True,
                behavioral_only=True,
            ),
        )

    @property
    def metadata(self) -> ComparatorMetadata:
        return self._metadata

    @staticmethod
    def _canonicalize(source: str) -> str:
        root = ET.fromstring(source)

        def normalize(node: ET.Element) -> str:
            attrs = "".join(f' {key}="{node.attrib[key]}"' for key in sorted(node.attrib))
            text = (node.text or "").strip()
            children = "".join(normalize(child) for child in list(node))
            tail = (node.tail or "").strip()
            return f"<{node.tag}{attrs}>{text}{children}</{node.tag}>{tail}"

        return normalize(root)

    def compare(
        self,
        *,
        expected: ExpectedOutput,
        generated: GeneratedOutput,
    ) -> ComparatorResult:
        try:
            left = self._canonicalize(expected.text)
            right = self._canonicalize(generated.text)
        except ET.ParseError as exc:
            return ComparatorResult(
                passed=False,
                similarity=None,
                message=f"XML parse failed: {exc}",
                findings=("xml_parse_error",),
                metadata={
                    "implemented": True,
                    "kind": ComparatorKind.XML.value,
                    "error": str(exc),
                },
            )
        passed = left == right
        return ComparatorResult(
            passed=passed,
            similarity=1.0 if passed else 0.0,
            message="XML match." if passed else "XML mismatch.",
            findings=("xml_match",) if passed else ("xml_mismatch",),
            metadata={"implemented": True, "kind": ComparatorKind.XML.value},
        )


class JsonComparator:
    """Compare JSON via parsed canonical dumps (key-order independent)."""

    def __init__(self) -> None:
        self._metadata = ComparatorMetadata(
            comparator_id="comparator.json",
            kind=ComparatorKind.JSON,
            name="JSON Comparison",
            description="Compare JSON documents after canonical encoding.",
            version="1.0.0",
            capabilities=ComparatorCapability(
                implemented=True,
                requires_json=True,
                supports_cpu=True,
                deterministic=True,
                behavioral_only=True,
            ),
        )

    @property
    def metadata(self) -> ComparatorMetadata:
        return self._metadata

    @staticmethod
    def _canonicalize(source: str) -> str:
        payload = json.loads(source)
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def compare(
        self,
        *,
        expected: ExpectedOutput,
        generated: GeneratedOutput,
    ) -> ComparatorResult:
        try:
            left = self._canonicalize(expected.text)
            right = self._canonicalize(generated.text)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            return ComparatorResult(
                passed=False,
                similarity=None,
                message=f"JSON parse failed: {exc}",
                findings=("json_parse_error",),
                metadata={
                    "implemented": True,
                    "kind": ComparatorKind.JSON.value,
                    "error": str(exc),
                },
            )
        passed = left == right
        return ComparatorResult(
            passed=passed,
            similarity=1.0 if passed else 0.0,
            message="JSON match." if passed else "JSON mismatch.",
            findings=("json_match",) if passed else ("json_mismatch",),
            metadata={"implemented": True, "kind": ComparatorKind.JSON.value},
        )


class TokenSimilarityComparator:
    """
    Whitespace-token Jaccard similarity (deterministic, no embeddings).

    Passes only when similarity == 1.0 (identical token multisets).
    """

    def __init__(self, *, pass_threshold: float = 1.0) -> None:
        self._pass_threshold = pass_threshold
        self._metadata = ComparatorMetadata(
            comparator_id="comparator.token_similarity",
            kind=ComparatorKind.TOKEN_SIMILARITY,
            name="Token Similarity",
            description="Jaccard similarity over whitespace tokens.",
            version="1.0.0",
            capabilities=ComparatorCapability(
                implemented=True,
                requires_tokenization=True,
                supports_cpu=True,
                deterministic=True,
                behavioral_only=True,
            ),
        )

    @property
    def metadata(self) -> ComparatorMetadata:
        return self._metadata

    @staticmethod
    def _tokens(text: str) -> Counter[str]:
        return Counter(text.split())

    def compare(
        self,
        *,
        expected: ExpectedOutput,
        generated: GeneratedOutput,
    ) -> ComparatorResult:
        left = self._tokens(expected.text)
        right = self._tokens(generated.text)
        if not left and not right:
            similarity = 1.0
        else:
            intersection = sum((left & right).values())
            union = sum((left | right).values())
            similarity = float(intersection) / float(union) if union else 0.0
        passed = similarity >= self._pass_threshold
        return ComparatorResult(
            passed=passed,
            similarity=similarity,
            message=(f"Token similarity {similarity:.3f} (threshold={self._pass_threshold:.3f})."),
            findings=("token_similarity_pass",) if passed else ("token_similarity_fail",),
            metadata={
                "implemented": True,
                "kind": ComparatorKind.TOKEN_SIMILARITY.value,
                "threshold": self._pass_threshold,
            },
        )


__all__ = [
    "AstComparator",
    "JsonComparator",
    "TokenSimilarityComparator",
    "XmlComparator",
]

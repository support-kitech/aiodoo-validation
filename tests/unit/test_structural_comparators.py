"""Unit tests for deterministic structural comparators."""

from __future__ import annotations

from aiodoo_validation.comparators import (
    AstComparator,
    JsonComparator,
    TokenSimilarityComparator,
    XmlComparator,
)
from aiodoo_validation.domain.behavior import ExpectedOutput, GeneratedOutput


def test_ast_comparator_ignores_formatting() -> None:
    expected = ExpectedOutput(text="def f(x):\n    return x + 1\n")
    generated = GeneratedOutput(text="def f(x): return x+1\n")
    result = AstComparator().compare(expected=expected, generated=generated)
    assert result.passed is True
    assert result.similarity == 1.0


def test_ast_comparator_detects_semantic_structure_change() -> None:
    expected = ExpectedOutput(text="def f(x):\n    return x + 1\n")
    generated = GeneratedOutput(text="def f(x):\n    return x + 2\n")
    result = AstComparator().compare(expected=expected, generated=generated)
    assert result.passed is False


def test_ast_comparator_handles_syntax_error() -> None:
    result = AstComparator().compare(
        expected=ExpectedOutput(text="def f(:\n"),
        generated=GeneratedOutput(text="def f():\n    pass\n"),
    )
    assert result.passed is False
    assert "ast_parse_error" in result.findings


def test_xml_comparator_ignores_attribute_order() -> None:
    expected = ExpectedOutput(text='<record id="a" model="res.partner"/>')
    generated = GeneratedOutput(text='<record model="res.partner" id="a"></record>')
    result = XmlComparator().compare(expected=expected, generated=generated)
    assert result.passed is True


def test_xml_comparator_detects_mismatch() -> None:
    result = XmlComparator().compare(
        expected=ExpectedOutput(text='<record id="a"/>'),
        generated=GeneratedOutput(text='<record id="b"/>'),
    )
    assert result.passed is False


def test_json_comparator_ignores_key_order() -> None:
    expected = ExpectedOutput(text='{"b": 2, "a": 1}')
    generated = GeneratedOutput(text='{"a": 1, "b": 2}')
    result = JsonComparator().compare(expected=expected, generated=generated)
    assert result.passed is True


def test_json_comparator_handles_invalid_json() -> None:
    result = JsonComparator().compare(
        expected=ExpectedOutput(text="{"),
        generated=GeneratedOutput(text='{"a": 1}'),
    )
    assert result.passed is False
    assert "json_parse_error" in result.findings


def test_token_similarity_identical_and_partial() -> None:
    expected = ExpectedOutput(text="alpha beta gamma")
    identical = GeneratedOutput(text="alpha beta gamma")
    partial = GeneratedOutput(text="alpha beta")
    assert TokenSimilarityComparator().compare(
        expected=expected, generated=identical
    ).passed
    partial_result = TokenSimilarityComparator().compare(
        expected=expected, generated=partial
    )
    assert partial_result.passed is False
    assert partial_result.similarity is not None
    assert 0.0 < partial_result.similarity < 1.0

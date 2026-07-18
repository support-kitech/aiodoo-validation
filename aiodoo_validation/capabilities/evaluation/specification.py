"""Evaluation CapabilitySpecification instance (mirrors capability.yaml)."""

from __future__ import annotations

from pathlib import Path

from aiodoo_validation.domain.capability_spec import (
    CapabilitySpecification,
    CorpusRequirements,
    RuntimeRequirements,
)
from aiodoo_validation.domain.enums import CorpusRole, ValidationKind

CAPABILITY_YAML_NAME = "capability.yaml"
EVALUATION_CAPABILITY_ID = "evaluation"
EVALUATION_PARSER_ID = "evaluation_v1"
EVALUATION_CORPUS_SCHEMA_ID = "evaluation_tasks_v1"


def capability_yaml_path() -> Path:
    """Path to the declarative Evaluation capability.yaml."""
    return Path(__file__).resolve().parent / CAPABILITY_YAML_NAME


def build_evaluation_specification() -> CapabilitySpecification:
    """
    Construct the frozen Evaluation Capability Specification.

    Values match ``capability.yaml``. Loaded in Python because base runtime
    dependencies do not include a YAML parser (same rationale as Repair).
    """
    return CapabilitySpecification(
        id=EVALUATION_CAPABILITY_ID,
        name="Evaluation",
        description="Independent evaluation capability adapter validation",
        version="1.0.0",
        supported_artifact_types=("base_model", "coding_adapter"),
        supported_languages=("python", "xml"),
        supported_transformation_types=("replace",),
        supported_comparator_kinds=(
            "exact",
            "json",
            "ast",
            "xml",
            "token_similarity",
        ),
        supported_evaluation_dimensions=(
            "transform_correctness",
            "syntax",
            "minimal_change",
            "intent_preservation",
            "hallucination",
            "explanation",
            "safety",
        ),
        supported_certification_kinds=(
            ValidationKind.STRUCTURAL.value,
            ValidationKind.BEHAVIORAL.value,
        ),
        corpus_schema_id=EVALUATION_CORPUS_SCHEMA_ID,
        corpus_requirements=CorpusRequirements(
            role=CorpusRole.EVALUATION,
            fingerprint_required=True,
        ),
        default_scoring_policy_ref="scoring_policy.yaml",
        default_certification_policy_ref="certification_defaults.yaml",
        runtime_requirements=RuntimeRequirements(
            behavior_certification="real_inference",
        ),
        parser_id=EVALUATION_PARSER_ID,
    )


__all__ = [
    "CAPABILITY_YAML_NAME",
    "EVALUATION_CAPABILITY_ID",
    "EVALUATION_CORPUS_SCHEMA_ID",
    "EVALUATION_PARSER_ID",
    "build_evaluation_specification",
    "capability_yaml_path",
]

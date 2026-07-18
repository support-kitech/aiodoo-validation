"""E7 integration — production corpus pin resolution via profile plans."""

from __future__ import annotations

from pathlib import Path

from aiodoo_validation.corpus import (
    EVALUATION_CORPUS_ID_KEY,
    EVALUATION_CORPUS_PATH_KEY,
    REPAIR_EVAL_FIXTURE_CORPUS_ID,
    ProductionCorpusLookup,
)
from aiodoo_validation.domain.artifacts import ArtifactBundle, ArtifactDescriptor
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ArtifactType, ExecutionTier, FingerprintPolicy
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.profiles.adapter_profile import AdapterProfile

REPAIR_EVAL = (
    Path(__file__).resolve().parents[1] / "fixtures" / "capabilities" / "repair" / "eval_corpus"
)


def _repair_bundle() -> ArtifactBundle:
    return ArtifactBundle(
        base_model=ArtifactDescriptor(
            artifact_type=ArtifactType.BASE_MODEL,
            logical_ref="base",
            location_digest="x",
            metadata={"identifier": "qwen"},
        ),
        adapter=ArtifactDescriptor(
            artifact_type=ArtifactType.CODING_ADAPTER,
            logical_ref="adapter",
            location_digest="y",
            metadata={"adapter_type": "repair"},
        ),
        merged_model=None,
        protocol_major=1,
        protocol_minor=0,
        fingerprint_policy=FingerprintPolicy.OFF,
        bundle_digest="e7",
    )


def test_production_lookup_and_plan_agree_on_pin() -> None:
    lookup = ProductionCorpusLookup().lookup(
        "repair.eval",
        capability_id="repair",
    )
    request = ValidationRequest(
        profile_name="repair",
        base_model_ref="./base",
        adapter_ref="./adapter",
        execution_tier=ExecutionTier.SMOKE,
        metadata={EVALUATION_CORPUS_ID_KEY: "repair.eval"},
    )
    plan = AdapterProfile.create("repair", odoo_versions=(18,)).build_validation_plan(
        bundle=_repair_bundle(),
        context=RunContext.begin(request),
    )
    assert lookup.corpus_ref == REPAIR_EVAL_FIXTURE_CORPUS_ID
    assert plan.configuration[EVALUATION_CORPUS_ID_KEY] == lookup.corpus_ref
    assert Path(plan.configuration[EVALUATION_CORPUS_PATH_KEY]) == lookup.location
    assert lookup.location == REPAIR_EVAL.resolve()

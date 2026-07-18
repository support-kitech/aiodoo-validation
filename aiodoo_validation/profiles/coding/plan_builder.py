"""Build ValidationPlan instances for the coding profile."""

from __future__ import annotations

import hashlib

from aiodoo_validation.corpus.governance import resolve_evaluation_corpus_configuration
from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ValidationStage
from aiodoo_validation.profiles.coding.profile import CodingProfile
from aiodoo_validation.validation_plan import ValidationPlan


def build_coding_validation_plan(
    profile: CodingProfile,
    *,
    bundle: ArtifactBundle,
    context: RunContext,
) -> ValidationPlan:
    """Construct an immutable coding ValidationPlan from profile metadata."""
    digest_material = "|".join(
        (
            profile.profile_name,
            bundle.bundle_digest,
            context.execution_tier.value,
            str(context.protocol_major),
        )
    )
    plan_digest = hashlib.sha256(digest_material.encode("utf-8")).hexdigest()[:16]
    execution_order = (
        ValidationStage.INITIALIZE_INFERENCE,
        ValidationStage.RUN_VALIDATION,
        ValidationStage.SCORING,
        ValidationStage.BENCHMARK,
        ValidationStage.CERTIFICATION,
        ValidationStage.REPORT,
    )
    return ValidationPlan(
        profile_name=profile.profile_name,
        plan_digest=plan_digest,
        capabilities=profile.capabilities,
        supported_artifact_types=profile.supported_artifact_types,
        supported_runtimes=profile.supported_runtimes,
        oracle_pipeline=profile.oracle_pipeline,
        scoring_pipeline=profile.scoring_pipeline,
        benchmark_pipeline=profile.benchmark_pipeline,
        certification_pipeline=profile.certification_pipeline,
        report_pipeline=profile.report_pipeline,
        execution_order=execution_order,
        validation_stages=(ValidationStage.RUN_VALIDATION,),
        configuration={
            "execution_tier": context.execution_tier.value,
            "protocol_major": context.protocol_major,
            "protocol_minor": context.protocol_minor,
            "odoo_versions": context.request.odoo_versions,
            "bundle_digest": bundle.bundle_digest,
            **dict(
                resolve_evaluation_corpus_configuration(
                    capability_id=profile.profile_name,
                    metadata=context.request.metadata,
                )
            ),
        },
    )

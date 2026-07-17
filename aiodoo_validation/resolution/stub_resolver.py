"""Stub artifact resolver (Phase 2)."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from aiodoo_validation.domain.artifacts import ArtifactDescriptor, ArtifactFingerprint
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ArtifactType
from aiodoo_validation.domain.resolution import ArtifactResolutionOutcome
from aiodoo_validation.resolution.common import build_artifact_bundle, effective_fingerprint_policy


@dataclass(frozen=True, slots=True)
class StubArtifactResolver:
    """Placeholder artifact resolver without filesystem access."""

    def resolve(self, context: RunContext) -> ArtifactResolutionOutcome:
        request = context.request
        policy = effective_fingerprint_policy(request)
        stub_fingerprint = ArtifactFingerprint(value="placeholder:stub", placeholder=True)

        base_model = ArtifactDescriptor(
            artifact_type=ArtifactType.BASE_MODEL,
            logical_ref="base_model",
            location_digest=stub_fingerprint.value,
            metadata=MappingProxyType(
                {
                    "stub": True,
                    "logical_ref": request.base_model_ref,
                    "protocol_major": request.protocol_major,
                }
            ),
            fingerprint=stub_fingerprint,
        )
        adapter = ArtifactDescriptor(
            artifact_type=ArtifactType.CODING_ADAPTER,
            logical_ref="adapter",
            location_digest="placeholder:stub-adapter",
            metadata=MappingProxyType(
                {
                    "stub": True,
                    "logical_ref": request.adapter_ref,
                    "adapter_type": "coding",
                    "protocol_major": request.protocol_major,
                }
            ),
            fingerprint=ArtifactFingerprint(value="placeholder:stub-adapter", placeholder=True),
        )
        merged_model = None
        if request.merged_model_ref:
            merged_model = ArtifactDescriptor(
                artifact_type=ArtifactType.MERGED_MODEL,
                logical_ref="merged_model",
                location_digest="placeholder:stub-merged",
                metadata=MappingProxyType(
                    {
                        "stub": True,
                        "logical_ref": request.merged_model_ref,
                        "protocol_major": request.protocol_major,
                    }
                ),
                fingerprint=ArtifactFingerprint(value="placeholder:stub-merged", placeholder=True),
            )

        bundle = build_artifact_bundle(
            request,
            base_model=base_model,
            adapter=adapter,
            merged_model=merged_model,
            fingerprint_policy=policy,
            metadata={"resolver": "stub", "stub": True},
        )
        return ArtifactResolutionOutcome(
            success=True,
            message="stub artifact resolution",
            bundle=bundle,
        )

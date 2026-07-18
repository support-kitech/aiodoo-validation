"""Placeholder certification policies (Phase 8 — no production rules)."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.benchmark.ids import (
    CODING_BENCHMARK_BEHAVIOR,
    CODING_BENCHMARK_MANIFEST,
    CODING_BENCHMARK_METADATA,
    CODING_BENCHMARK_MODULE_STRUCTURE,
    CODING_BENCHMARK_PYTHON,
    CODING_BENCHMARK_QUALITY,
    CODING_BENCHMARK_SECURITY,
    CODING_BENCHMARK_XML,
)
from aiodoo_validation.certification.ids import (
    CODING_CERTIFICATION_BEHAVIOR,
    CODING_CERTIFICATION_MANIFEST,
    CODING_CERTIFICATION_METADATA,
    CODING_CERTIFICATION_MODULE_STRUCTURE,
    CODING_CERTIFICATION_PYTHON,
    CODING_CERTIFICATION_QUALITY,
    CODING_CERTIFICATION_SECURITY,
    CODING_CERTIFICATION_XML,
    PLACEHOLDER_CERTIFICATION_LEVEL,
    PLACEHOLDER_CERTIFICATION_SCORE,
    PLACEHOLDER_CERTIFIED,
)
from aiodoo_validation.domain.certification import (
    CertificationCapability,
    CertificationContext,
    CertificationMetadata,
    CertificationResult,
)


def placeholder_certification_metadata(
    *,
    policy_id: str,
    name: str,
    description: str,
    source_benchmark_policy_id: str,
    supported_profile: str = "coding",
    version: str = "0.0.0-placeholder",
) -> CertificationMetadata:
    return CertificationMetadata(
        policy_id=policy_id,
        name=name,
        description=description,
        version=version,
        supported_profile=supported_profile,
        source_benchmark_policy_id=source_benchmark_policy_id,
        capabilities=CertificationCapability(
            placeholder=True,
            consumes_benchmark_result=True,
            inspects_filesystem=False,
            applies_thresholds=False,
        ),
    )


@dataclass(frozen=True, slots=True)
class PlaceholderCertificationPolicy:
    """Base placeholder policy returning deterministic certification values."""

    metadata: CertificationMetadata

    def certify(self, context: CertificationContext) -> CertificationResult:
        started = perf_counter()
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        return CertificationResult(
            policy_id=self.metadata.policy_id,
            source_benchmark_policy_id=self.metadata.source_benchmark_policy_id,
            success=True,
            certified=PLACEHOLDER_CERTIFIED,
            certification_score=PLACEHOLDER_CERTIFICATION_SCORE,
            certification_level=PLACEHOLDER_CERTIFICATION_LEVEL,
            message=(
                f"Placeholder certification policy {self.metadata.policy_id!r} "
                f"certified benchmark policy {context.benchmark_result.policy_id!r}."
            ),
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": True,
                    "benchmark_score": context.benchmark_result.benchmark_score,
                    "benchmark_pass": context.benchmark_result.benchmark_pass,
                    "plan_digest": context.plan_digest,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class MetadataCertificationPolicy(PlaceholderCertificationPolicy):
    @staticmethod
    def create() -> MetadataCertificationPolicy:
        return MetadataCertificationPolicy(
            metadata=placeholder_certification_metadata(
                policy_id=CODING_CERTIFICATION_METADATA,
                name="Metadata Certification Policy",
                description="Placeholder metadata certification policy.",
                source_benchmark_policy_id=CODING_BENCHMARK_METADATA,
            )
        )


@dataclass(frozen=True, slots=True)
class ManifestCertificationPolicy(PlaceholderCertificationPolicy):
    @staticmethod
    def create() -> ManifestCertificationPolicy:
        return ManifestCertificationPolicy(
            metadata=placeholder_certification_metadata(
                policy_id=CODING_CERTIFICATION_MANIFEST,
                name="Manifest Certification Policy",
                description="Placeholder manifest certification policy.",
                source_benchmark_policy_id=CODING_BENCHMARK_MANIFEST,
            )
        )


@dataclass(frozen=True, slots=True)
class PythonCertificationPolicy(PlaceholderCertificationPolicy):
    @staticmethod
    def create() -> PythonCertificationPolicy:
        return PythonCertificationPolicy(
            metadata=placeholder_certification_metadata(
                policy_id=CODING_CERTIFICATION_PYTHON,
                name="Python Certification Policy",
                description="Placeholder Python certification policy.",
                source_benchmark_policy_id=CODING_BENCHMARK_PYTHON,
            )
        )


@dataclass(frozen=True, slots=True)
class XmlCertificationPolicy(PlaceholderCertificationPolicy):
    @staticmethod
    def create() -> XmlCertificationPolicy:
        return XmlCertificationPolicy(
            metadata=placeholder_certification_metadata(
                policy_id=CODING_CERTIFICATION_XML,
                name="XML Certification Policy",
                description="Placeholder XML certification policy.",
                source_benchmark_policy_id=CODING_BENCHMARK_XML,
            )
        )


@dataclass(frozen=True, slots=True)
class SecurityCertificationPolicy(PlaceholderCertificationPolicy):
    @staticmethod
    def create() -> SecurityCertificationPolicy:
        return SecurityCertificationPolicy(
            metadata=placeholder_certification_metadata(
                policy_id=CODING_CERTIFICATION_SECURITY,
                name="Security Certification Policy",
                description="Placeholder security certification policy.",
                source_benchmark_policy_id=CODING_BENCHMARK_SECURITY,
            )
        )


@dataclass(frozen=True, slots=True)
class ModuleStructureCertificationPolicy(PlaceholderCertificationPolicy):
    @staticmethod
    def create() -> ModuleStructureCertificationPolicy:
        return ModuleStructureCertificationPolicy(
            metadata=placeholder_certification_metadata(
                policy_id=CODING_CERTIFICATION_MODULE_STRUCTURE,
                name="Module Structure Certification Policy",
                description="Placeholder module structure certification policy.",
                source_benchmark_policy_id=CODING_BENCHMARK_MODULE_STRUCTURE,
            )
        )


@dataclass(frozen=True, slots=True)
class QualityCertificationPolicy(PlaceholderCertificationPolicy):
    """Future quality certification policy (available for plugins; disabled in plan)."""

    @staticmethod
    def create() -> QualityCertificationPolicy:
        return QualityCertificationPolicy(
            metadata=placeholder_certification_metadata(
                policy_id=CODING_CERTIFICATION_QUALITY,
                name="Quality Certification Policy",
                description="Placeholder future quality certification policy.",
                source_benchmark_policy_id=CODING_BENCHMARK_QUALITY,
            )
        )


@dataclass(frozen=True, slots=True)
class BehaviorCertificationPolicy(PlaceholderCertificationPolicy):
    """Placeholder coding behavior certification policy (stub path)."""

    @staticmethod
    def create() -> BehaviorCertificationPolicy:
        return BehaviorCertificationPolicy(
            metadata=placeholder_certification_metadata(
                policy_id=CODING_CERTIFICATION_BEHAVIOR,
                name="Coding Behavior Certification Policy",
                description="Placeholder coding behavior certification policy.",
                source_benchmark_policy_id=CODING_BENCHMARK_BEHAVIOR,
            )
        )


def default_coding_placeholder_policies() -> tuple[PlaceholderCertificationPolicy, ...]:
    return (
        MetadataCertificationPolicy.create(),
        ManifestCertificationPolicy.create(),
        PythonCertificationPolicy.create(),
        XmlCertificationPolicy.create(),
        SecurityCertificationPolicy.create(),
        ModuleStructureCertificationPolicy.create(),
        BehaviorCertificationPolicy.create(),
    )

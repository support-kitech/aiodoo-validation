"""Capability behavior pipeline — assemble cases and verify gold transforms (E5)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.behavior.build_result import BehaviorCaseBuildResult
from aiodoo_validation.behavior.case_builder import BehaviorCaseBuilder
from aiodoo_validation.capabilities.contract import RegisteredCapabilityPack
from aiodoo_validation.corpus.loader import LoadedCorpus
from aiodoo_validation.domain.behavior import BehaviorCase, BehaviorCorpus
from aiodoo_validation.domain.capability_record import ParsedCapabilityRecord
from aiodoo_validation.exceptions import AiodooValidationError
from aiodoo_validation.transforms.comparator import SnapshotComparator
from aiodoo_validation.transforms.engine import TransformationEngine
from aiodoo_validation.transforms.snapshot import ArtifactSnapshot


class CapabilityPipelineError(AiodooValidationError):
    """Raised when capability corpus assembly fails."""


@dataclass(frozen=True, slots=True)
class TransformVerificationResult:
    """Outcome of applying gold transforms and comparing snapshots."""

    success: bool
    findings: tuple[str, ...]
    message: str
    occurrence_count: int = 0
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class AssembledCapabilityCorpus:
    """Behavior corpus plus per-case transform verification."""

    corpus: BehaviorCorpus
    build_results: tuple[BehaviorCaseBuildResult, ...]
    transform_results: tuple[TransformVerificationResult, ...]
    loaded: LoadedCorpus

    @property
    def transforms_passed(self) -> bool:
        return all(item.success for item in self.transform_results)


@dataclass(frozen=True, slots=True)
class CapabilityBehaviorPipeline:
    """
    Orchestrate pack parse → BehaviorCaseBuilder → transform verify.

    Does not run BehaviorRunner (caller does). Does not load corpora (caller does).
    """

    case_builder: BehaviorCaseBuilder = field(default_factory=BehaviorCaseBuilder)
    transformation_engine: TransformationEngine = field(default_factory=TransformationEngine)
    snapshot_comparator: SnapshotComparator = field(default_factory=SnapshotComparator)

    def assemble(
        self,
        loaded: LoadedCorpus,
        pack: RegisteredCapabilityPack,
    ) -> AssembledCapabilityCorpus:
        if loaded.manifest.capability_id != pack.capability_id:
            raise CapabilityPipelineError(
                f"Corpus capability_id {loaded.manifest.capability_id!r} does not "
                f"match registered pack {pack.capability_id!r}."
            )

        build_results: list[BehaviorCaseBuildResult] = []
        transform_results: list[TransformVerificationResult] = []
        cases: list[BehaviorCase] = []

        for index, raw in enumerate(loaded.records):
            if not isinstance(raw, Mapping):
                raise CapabilityPipelineError(f"Corpus record {index} must be a JSON object.")
            parsed_records = self._parse_records(pack, raw, index=index)
            for parsed in parsed_records:
                built = self.case_builder.build(parsed, pack.specification)
                verification = self.verify_transforms(built)
                annotated = self._annotate_case(built.case, verification)
                build_results.append(built)
                transform_results.append(verification)
                cases.append(annotated)

        corpus = BehaviorCorpus(
            corpus_id=loaded.manifest.corpus_id,
            profile_name=pack.capability_id,
            cases=tuple(cases),
            metadata=MappingProxyType(
                {
                    "capability_id": pack.capability_id,
                    "fingerprint": loaded.manifest.fingerprint,
                    "computed_fingerprint": loaded.computed_fingerprint,
                    "dataset_version": loaded.manifest.dataset_version,
                    "source_package": loaded.manifest.source_package,
                    "record_count": len(loaded.records),
                    "case_count": len(cases),
                }
            ),
        )
        return AssembledCapabilityCorpus(
            corpus=corpus,
            build_results=tuple(build_results),
            transform_results=tuple(transform_results),
            loaded=loaded,
        )

    def verify_transforms(
        self,
        built: BehaviorCaseBuildResult,
    ) -> TransformVerificationResult:
        if not built.transformations:
            return TransformVerificationResult(
                success=True,
                findings=("no_transformations",),
                message="No gold transformations to verify.",
                occurrence_count=0,
            )

        snapshot: ArtifactSnapshot = built.original_snapshot
        total_occurrences = 0
        findings: list[str] = []
        for index, transform in enumerate(built.transformations):
            result = self.transformation_engine.apply(snapshot, transform)
            if not result.success:
                findings.extend(result.findings)
                return TransformVerificationResult(
                    success=False,
                    findings=tuple(findings) or ("transform_apply_failed",),
                    message=(
                        f"Gold transform {index} failed for case "
                        f"{built.record_id!r}: {result.message}"
                    ),
                    occurrence_count=total_occurrences,
                    metadata={"failed_index": index},
                )
            total_occurrences += result.occurrence_count
            findings.extend(result.findings)
            snapshot = result.snapshot

        has_expected_artifacts = built.case.expected.metadata.get("source") == "expected_artifacts"
        if has_expected_artifacts:
            comparison = self.snapshot_comparator.compare(
                original=built.original_snapshot,
                transformed=snapshot,
                expected=built.expected_snapshot,
            )
            if not comparison.passed:
                return TransformVerificationResult(
                    success=False,
                    findings=tuple(findings) + comparison.findings,
                    message=(
                        f"Transformed snapshot does not match expected for case "
                        f"{built.record_id!r}."
                    ),
                    occurrence_count=total_occurrences,
                    metadata={"comparator_passed": False},
                )
            findings = list(findings) + list(comparison.findings)

        return TransformVerificationResult(
            success=True,
            findings=tuple(findings) or ("transforms_verified",),
            message=(
                f"Applied {len(built.transformations)} gold transform(s) "
                f"({total_occurrences} replacement(s))."
            ),
            occurrence_count=total_occurrences,
            metadata={"comparator_used": has_expected_artifacts},
        )

    def _parse_records(
        self,
        pack: RegisteredCapabilityPack,
        raw: Mapping[str, Any],
        *,
        index: int,
    ) -> tuple[ParsedCapabilityRecord, ...]:
        try:
            if "output" in raw and "instruction" in raw:
                return pack.parser.parse_training_example(raw)
            return (pack.parser.parse(raw),)
        except Exception as exc:  # noqa: BLE001 — surface pack/parser errors with context
            raise CapabilityPipelineError(
                f"Failed to parse corpus record {index} for capability "
                f"{pack.capability_id!r}: {exc}"
            ) from exc

    @staticmethod
    def _annotate_case(
        case: BehaviorCase,
        verification: TransformVerificationResult,
    ) -> BehaviorCase:
        metadata = dict(case.metadata)
        metadata["transform_verification"] = {
            "success": verification.success,
            "findings": list(verification.findings),
            "message": verification.message,
            "occurrence_count": verification.occurrence_count,
        }
        return BehaviorCase(
            case_id=case.case_id,
            prompt=case.prompt,
            expected=case.expected,
            comparator_kind=case.comparator_kind,
            tags=case.tags,
            metadata=MappingProxyType(metadata),
        )


__all__ = [
    "AssembledCapabilityCorpus",
    "CapabilityBehaviorPipeline",
    "CapabilityPipelineError",
    "TransformVerificationResult",
]

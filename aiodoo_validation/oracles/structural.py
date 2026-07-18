"""Production structural oracles — inspect real resolved artifacts.

These replace placeholder always-succeed oracles for the filesystem CLI path.
They do not invent Odoo semantic evaluation (XML AST, security scanners, etc.):
those require dedicated evaluation corpora. They do validate on-disk contracts
required for certification handoff.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.domain.artifact_paths import ARTIFACT_PATHS_KEY
from aiodoo_validation.domain.oracle import (
    OracleCapability,
    OracleContext,
    OracleMetadata,
    OracleResult,
)


def _paths_from_context(context: OracleContext) -> tuple[Path | None, Path | None]:
    bundle = context.artifact_bundle
    if bundle is None:
        return None, None
    raw = bundle.metadata.get(ARTIFACT_PATHS_KEY)
    if not isinstance(raw, dict):
        return None, None
    base = raw.get("base_model")
    adapter = raw.get("adapter")
    base_path = Path(base) if isinstance(base, str) else None
    adapter_path = Path(adapter) if isinstance(adapter, str) else None
    return base_path, adapter_path


def _production_metadata(
    *,
    oracle_id: str,
    name: str,
    description: str,
    supported_profile: str,
) -> OracleMetadata:
    return OracleMetadata(
        oracle_id=oracle_id,
        name=name,
        description=description,
        version="1.0.0",
        supported_profile=supported_profile,
        capabilities=OracleCapability(
            placeholder=False,
            reads_artifacts=True,
            uses_inference=False,
        ),
    )


@dataclass(frozen=True, slots=True)
class StructuralOracle:
    """Base structural oracle with shared path helpers."""

    metadata: OracleMetadata

    def execute(self, context: OracleContext) -> OracleResult:
        started = perf_counter()
        success, message, findings = self._evaluate(context)
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        return OracleResult(
            oracle_id=self.metadata.oracle_id,
            success=success,
            message=message,
            findings=findings,
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": False,
                    "profile_name": context.profile_name,
                    "plan_digest": context.plan_digest,
                    "execution_tier": context.execution_tier.value,
                }
            ),
        )

    def _evaluate(self, context: OracleContext) -> tuple[bool, str, tuple[str, ...]]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class MetadataStructuralOracle(StructuralOracle):
    def _evaluate(self, context: OracleContext) -> tuple[bool, str, tuple[str, ...]]:
        bundle = context.artifact_bundle
        if bundle is None:
            return False, "Artifact bundle missing.", ("missing_bundle",)
        findings: list[str] = []
        base = bundle.base_model.metadata
        adapter = bundle.adapter.metadata
        if base.get("artifact_type") != "base_model":
            findings.append("base_model.artifact_type invalid")
        if not base.get("identifier") and not base.get("model_id"):
            findings.append("base_model.identifier missing")
        if adapter.get("artifact_type") != "coding_adapter":
            findings.append("adapter.artifact_type invalid")
        adapter_type = str(adapter.get("adapter_type", "")).strip().lower()
        if adapter_type and adapter_type != context.profile_name.strip().lower():
            findings.append(
                f"adapter_type {adapter_type!r} does not match profile "
                f"{context.profile_name!r}"
            )
        if findings:
            return False, "Metadata oracle failed.", tuple(findings)
        return True, "Metadata oracle passed.", ("metadata_ok",)


@dataclass(frozen=True, slots=True)
class ManifestStructuralOracle(StructuralOracle):
    def _evaluate(self, context: OracleContext) -> tuple[bool, str, tuple[str, ...]]:
        _, adapter = _paths_from_context(context)
        if adapter is None or not adapter.is_dir():
            return False, "Adapter path missing.", ("adapter_path_missing",)
        required = ("artifact.json", "adapter_config.json")
        missing = [name for name in required if not (adapter / name).is_file()]
        # Weights may be .safetensors or .bin
        has_weights = any(adapter.glob("adapter_model.*")) or any(
            adapter.glob("*.safetensors")
        )
        if not has_weights:
            missing.append("adapter weights")
        if missing:
            return False, "Manifest oracle failed.", tuple(f"missing:{m}" for m in missing)
        return True, "Manifest oracle passed.", ("manifest_ok",)


@dataclass(frozen=True, slots=True)
class AdapterFilesStructuralOracle(StructuralOracle):
    """Shared checks for python/xml/security/module_structure until domain corpora exist."""

    def _evaluate(self, context: OracleContext) -> tuple[bool, str, tuple[str, ...]]:
        base, adapter = _paths_from_context(context)
        if base is None or not base.is_dir():
            return False, "Base model path missing.", ("base_path_missing",)
        if adapter is None or not adapter.is_dir():
            return False, "Adapter path missing.", ("adapter_path_missing",)
        if not (base / "artifact.json").is_file():
            return False, "Base artifact.json missing.", ("base_artifact_json_missing",)
        if not (adapter / "artifact.json").is_file():
            return False, "Adapter artifact.json missing.", ("adapter_artifact_json_missing",)
        # Directory non-empty beyond metadata
        adapter_files = [p for p in adapter.iterdir() if p.is_file()]
        if len(adapter_files) < 2:
            return False, "Adapter directory incomplete.", ("adapter_incomplete",)
        return (
            True,
            f"{self.metadata.name} structural checks passed.",
            (f"{self.metadata.oracle_id}:ok",),
        )


def default_production_oracles(
    *,
    profile: str = "coding",
) -> tuple[StructuralOracle, ...]:
    """Build production structural oracles for ``{profile}.oracle.*`` IDs."""
    return (
        MetadataStructuralOracle(
            metadata=_production_metadata(
                oracle_id=f"{profile}.oracle.metadata",
                name="Metadata Oracle",
                description="Validate artifact.json contracts for base + adapter.",
                supported_profile=profile,
            )
        ),
        ManifestStructuralOracle(
            metadata=_production_metadata(
                oracle_id=f"{profile}.oracle.manifest",
                name="Manifest Oracle",
                description="Validate adapter publish files and weights.",
                supported_profile=profile,
            )
        ),
        AdapterFilesStructuralOracle(
            metadata=_production_metadata(
                oracle_id=f"{profile}.oracle.python",
                name="Python Oracle",
                description="Structural adapter/base readiness (domain corpus deferred).",
                supported_profile=profile,
            )
        ),
        AdapterFilesStructuralOracle(
            metadata=_production_metadata(
                oracle_id=f"{profile}.oracle.xml",
                name="XML Oracle",
                description="Structural adapter/base readiness (domain corpus deferred).",
                supported_profile=profile,
            )
        ),
        AdapterFilesStructuralOracle(
            metadata=_production_metadata(
                oracle_id=f"{profile}.oracle.security",
                name="Security Oracle",
                description="Structural adapter/base readiness (domain corpus deferred).",
                supported_profile=profile,
            )
        ),
        AdapterFilesStructuralOracle(
            metadata=_production_metadata(
                oracle_id=f"{profile}.oracle.module_structure",
                name="Module Structure Oracle",
                description="Structural adapter/base readiness (domain corpus deferred).",
                supported_profile=profile,
            )
        ),
    )


# Backward-compatible alias
def default_production_coding_oracles(
    *,
    supported_profile: str = "coding",
) -> tuple[StructuralOracle, ...]:
    return default_production_oracles(profile=supported_profile)


__all__ = [
    "AdapterFilesStructuralOracle",
    "ManifestStructuralOracle",
    "MetadataStructuralOracle",
    "StructuralOracle",
    "default_production_coding_oracles",
    "default_production_oracles",
]

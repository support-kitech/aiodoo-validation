"""E7 evaluation corpus governance and production pinning tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiodoo_validation.corpus import (
    EVALUATION_CORPUS_ID_KEY,
    EVALUATION_CORPUS_PATH_KEY,
    REPAIR_EVAL_FIXTURE_CORPUS_ID,
    ConfigurableCorpusProvider,
    CorpusGateError,
    CorpusLoadError,
    CorpusPin,
    CorpusPinError,
    CorpusPinRegistry,
    JsonlCorpusLoader,
    ProductionCorpusLookup,
    builtin_corpus_pin_registry,
    resolve_evaluation_corpus_configuration,
    resolve_pin_location,
    verify_loaded_corpus_against_pin,
)
from aiodoo_validation.domain.artifacts import ArtifactBundle, ArtifactDescriptor
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ArtifactType, ExecutionTier, FingerprintPolicy
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.profiles.adapter_profile import AdapterProfile

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
REPAIR_EVAL = FIXTURES / "capabilities" / "repair" / "eval_corpus"
REPAIR_TRAIN = FIXTURES / "capabilities" / "repair" / "eval_corpus_training"
CORPUS_VALID = FIXTURES / "corpus" / "valid_evaluation"
CORPUS_FP_MISMATCH = FIXTURES / "corpus" / "fingerprint_mismatch"


def _write_corpus(
    root: Path,
    *,
    corpus_id: str,
    capability_id: str,
    fingerprint: str,
    dataset_version: str = "v1",
    source_package: str | None = "pkg",
    records: list[dict] | None = None,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    payload = {
        "corpus_id": corpus_id,
        "capability_id": capability_id,
        "role": "evaluation",
        "dataset_version": dataset_version,
        "fingerprint": fingerprint,
        "denied_training_fingerprints": [],
        "metadata": {},
    }
    if source_package is not None:
        payload["source_package"] = source_package
    (root / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    lines = records or [{"id": "r1", "value": 1}]
    (root / "records.jsonl").write_text(
        "\n".join(json.dumps(item) for item in lines) + "\n",
        encoding="utf-8",
    )
    return root


class TestCorpusPinRegistry:
    def test_registry_lookup_and_alias(self) -> None:
        registry = builtin_corpus_pin_registry()
        pin = registry.get(REPAIR_EVAL_FIXTURE_CORPUS_ID)
        assert pin.capability_id == "repair"
        assert registry.get("repair.eval").corpus_id == REPAIR_EVAL_FIXTURE_CORPUS_ID
        assert registry.default_for_capability("repair") is not None

    def test_wrong_capability_rejected(self) -> None:
        registry = builtin_corpus_pin_registry()
        with pytest.raises(CorpusPinError, match="belongs to capability"):
            registry.require_for_capability(
                REPAIR_EVAL_FIXTURE_CORPUS_ID,
                capability_id="coding",
            )

    def test_unknown_identity(self) -> None:
        registry = builtin_corpus_pin_registry()
        with pytest.raises(CorpusPinError, match="Unknown corpus identity"):
            registry.get("does.not.exist")


class TestPinVerification:
    def test_valid_corpus_pin(self) -> None:
        lookup = ProductionCorpusLookup()
        result = lookup.lookup(
            REPAIR_EVAL_FIXTURE_CORPUS_ID,
            capability_id="repair",
        )
        assert result.loaded.manifest.corpus_id == REPAIR_EVAL_FIXTURE_CORPUS_ID
        assert result.location == REPAIR_EVAL.resolve()

    def test_fingerprint_mismatch_against_pin(self, tmp_path: Path) -> None:
        pin = builtin_corpus_pin_registry().get(REPAIR_EVAL_FIXTURE_CORPUS_ID)
        # Copy fixture records but declare wrong fingerprint in a synthetic pin.
        bad_pin = CorpusPin(
            corpus_id=pin.corpus_id,
            capability_id=pin.capability_id,
            fingerprint="0" * 64,
            dataset_version=pin.dataset_version,
            source_package=pin.source_package,
        )
        loaded = JsonlCorpusLoader().load(REPAIR_EVAL, purpose="test")
        with pytest.raises(CorpusPinError, match="fingerprint_mismatch_against_pin"):
            verify_loaded_corpus_against_pin(loaded, bad_pin)

    def test_loader_fingerprint_mismatch_still_fail_closed(self) -> None:
        with pytest.raises(CorpusGateError, match="fingerprint_mismatch"):
            JsonlCorpusLoader().load(CORPUS_FP_MISMATCH)

    def test_manifest_corpus_id_mismatch(self, tmp_path: Path) -> None:
        from aiodoo_validation.corpus.jsonl import fingerprint_file

        records = tmp_path / "records.jsonl"
        records.write_text('{"id":"a"}\n', encoding="utf-8")
        fp = fingerprint_file(records)
        corpus_dir = tmp_path / "corpus"
        _write_corpus(
            corpus_dir,
            corpus_id="other.id",
            capability_id="repair",
            fingerprint=fp,
            dataset_version="fixture-e5",
            source_package="aiodoo-validation-fixtures",
        )
        # Move records into corpus dir layout
        (corpus_dir / "records.jsonl").write_text(records.read_text(encoding="utf-8"))
        pin = builtin_corpus_pin_registry().get(REPAIR_EVAL_FIXTURE_CORPUS_ID)
        loaded = JsonlCorpusLoader().load(corpus_dir, purpose="test")
        with pytest.raises(CorpusPinError, match="corpus_id_mismatch"):
            verify_loaded_corpus_against_pin(loaded, pin)

    def test_version_mismatch(self) -> None:
        pin = CorpusPin(
            corpus_id=REPAIR_EVAL_FIXTURE_CORPUS_ID,
            capability_id="repair",
            fingerprint=builtin_corpus_pin_registry()
            .get(REPAIR_EVAL_FIXTURE_CORPUS_ID)
            .fingerprint,
            dataset_version="wrong-version",
            source_package="aiodoo-validation-fixtures",
        )
        loaded = JsonlCorpusLoader().load(REPAIR_EVAL, purpose="test")
        with pytest.raises(CorpusPinError, match="dataset_version_mismatch"):
            verify_loaded_corpus_against_pin(loaded, pin)

    def test_missing_corpus_location(self, tmp_path: Path) -> None:
        pin = CorpusPin(
            corpus_id="missing.corpus",
            capability_id="repair",
            fingerprint="a" * 64,
            dataset_version="v1",
            location_hint="nope",
        )
        with pytest.raises(CorpusLoadError, match="not found"):
            resolve_pin_location(pin, search_roots=(tmp_path,))


class TestProductionLookupAndProvider:
    def test_production_lookup_alias(self) -> None:
        result = ProductionCorpusLookup().lookup("repair.eval", capability_id="repair")
        assert result.corpus_ref == REPAIR_EVAL_FIXTURE_CORPUS_ID

    def test_provider_path_loads_and_verifies_known_pin(self) -> None:
        loaded = ConfigurableCorpusProvider().load(REPAIR_EVAL, capability_id="repair")
        assert loaded is not None
        assert loaded.manifest.corpus_id == REPAIR_EVAL_FIXTURE_CORPUS_ID

    def test_provider_unknown_corpus_path_still_loads(self) -> None:
        loaded = ConfigurableCorpusProvider().load(CORPUS_VALID, purpose="test")
        assert loaded is not None
        assert loaded.manifest.corpus_id == "fixture.repair.eval"

    def test_provider_load_by_identity(self) -> None:
        loaded = ConfigurableCorpusProvider().load_by_identity(
            "repair.eval.fixture",
            capability_id="repair",
        )
        assert loaded.manifest.fingerprint.startswith("dc418ad4")

    def test_provider_training_corpus_rejected(self) -> None:
        with pytest.raises(CorpusGateError):
            ConfigurableCorpusProvider().load(REPAIR_TRAIN)

    def test_provider_missing_path_defers(self) -> None:
        assert ConfigurableCorpusProvider().load(None) is None
        assert ConfigurableCorpusProvider().load("  ") is None

    def test_provider_wrong_capability_on_known_pin(self) -> None:
        with pytest.raises(CorpusPinError, match="not 'coding'"):
            ConfigurableCorpusProvider().load(REPAIR_EVAL, capability_id="coding")


class TestConfigurationResolution:
    def test_empty_metadata_defers(self) -> None:
        resolved = resolve_evaluation_corpus_configuration(
            capability_id="repair",
            metadata={},
        )
        assert dict(resolved) == {}

    def test_identity_resolves_to_path(self) -> None:
        resolved = resolve_evaluation_corpus_configuration(
            capability_id="repair",
            metadata={EVALUATION_CORPUS_ID_KEY: "repair.eval"},
        )
        assert resolved[EVALUATION_CORPUS_ID_KEY] == REPAIR_EVAL_FIXTURE_CORPUS_ID
        assert Path(resolved[EVALUATION_CORPUS_PATH_KEY]) == REPAIR_EVAL.resolve()

    def test_path_only_forwarded(self) -> None:
        resolved = resolve_evaluation_corpus_configuration(
            capability_id="repair",
            metadata={EVALUATION_CORPUS_PATH_KEY: str(CORPUS_VALID)},
        )
        assert EVALUATION_CORPUS_ID_KEY not in resolved
        assert resolved[EVALUATION_CORPUS_PATH_KEY] == str(CORPUS_VALID)

    def test_wrong_capability_identity(self) -> None:
        with pytest.raises(CorpusPinError):
            resolve_evaluation_corpus_configuration(
                capability_id="coding",
                metadata={EVALUATION_CORPUS_ID_KEY: REPAIR_EVAL_FIXTURE_CORPUS_ID},
            )

    def test_explicit_path_override_for_pin(self, tmp_path: Path) -> None:
        # Valid pin content copied to override location.
        override = tmp_path / "override"
        override.mkdir()
        for name in ("manifest.json", "records.jsonl"):
            (override / name).write_bytes((REPAIR_EVAL / name).read_bytes())
        resolved = resolve_evaluation_corpus_configuration(
            capability_id="repair",
            metadata={
                EVALUATION_CORPUS_ID_KEY: REPAIR_EVAL_FIXTURE_CORPUS_ID,
                EVALUATION_CORPUS_PATH_KEY: str(override),
            },
        )
        assert Path(resolved[EVALUATION_CORPUS_PATH_KEY]) == override.resolve()


class TestAdapterProfileIntegration:
    def _bundle(self) -> ArtifactBundle:
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
            bundle_digest="d1",
        )

    def test_plan_resolves_corpus_identity(self) -> None:
        request = ValidationRequest(
            profile_name="repair",
            base_model_ref="base",
            adapter_ref="adapter",
            execution_tier=ExecutionTier.SMOKE,
            metadata={EVALUATION_CORPUS_ID_KEY: "repair.eval"},
        )
        context = RunContext.begin(request)
        profile = AdapterProfile.create("repair", odoo_versions=(18,))
        plan = profile.build_validation_plan(bundle=self._bundle(), context=context)
        assert plan.configuration[EVALUATION_CORPUS_ID_KEY] == REPAIR_EVAL_FIXTURE_CORPUS_ID
        assert Path(plan.configuration[EVALUATION_CORPUS_PATH_KEY]) == REPAIR_EVAL.resolve()

    def test_plan_without_corpus_stays_empty(self) -> None:
        request = ValidationRequest(
            profile_name="repair",
            base_model_ref="base",
            adapter_ref="adapter",
            execution_tier=ExecutionTier.SMOKE,
        )
        context = RunContext.begin(request)
        profile = AdapterProfile.create("repair", odoo_versions=(18,))
        plan = profile.build_validation_plan(bundle=self._bundle(), context=context)
        assert EVALUATION_CORPUS_PATH_KEY not in plan.configuration
        assert EVALUATION_CORPUS_ID_KEY not in plan.configuration

    def test_plan_path_only_unchanged(self) -> None:
        request = ValidationRequest(
            profile_name="repair",
            base_model_ref="base",
            adapter_ref="adapter",
            metadata={EVALUATION_CORPUS_PATH_KEY: str(REPAIR_EVAL)},
        )
        context = RunContext.begin(request)
        profile = AdapterProfile.create("repair", odoo_versions=(18,))
        plan = profile.build_validation_plan(bundle=self._bundle(), context=context)
        assert plan.configuration[EVALUATION_CORPUS_PATH_KEY] == str(REPAIR_EVAL)
        assert EVALUATION_CORPUS_ID_KEY not in plan.configuration


class TestCustomRegistry:
    def test_custom_registry_build(self, tmp_path: Path) -> None:
        from aiodoo_validation.corpus.jsonl import fingerprint_file

        corpus = tmp_path / "custom"
        records = '{"id":1}\n'
        corpus.mkdir()
        (corpus / "records.jsonl").write_text(records, encoding="utf-8")
        fp = fingerprint_file(corpus / "records.jsonl")
        _write_corpus(
            corpus,
            corpus_id="custom.eval",
            capability_id="repair",
            fingerprint=fp,
            dataset_version="1.0.0",
        )
        (corpus / "records.jsonl").write_text(records, encoding="utf-8")
        pin = CorpusPin(
            corpus_id="custom.eval",
            capability_id="repair",
            fingerprint=fp,
            dataset_version="1.0.0",
            source_package="pkg",
        )
        registry = CorpusPinRegistry.build(
            (pin,),
            locations={"custom.eval": corpus},
        )
        result = ProductionCorpusLookup(registry=registry).lookup(
            "custom.eval",
            capability_id="repair",
        )
        assert result.loaded.manifest.corpus_id == "custom.eval"

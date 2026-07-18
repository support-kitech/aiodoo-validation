"""Fail-closed corpus gate evaluation (no I/O)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal

from aiodoo_validation.domain.corpus import CorpusManifest
from aiodoo_validation.domain.enums import CorpusRole

GatePurpose = Literal["production_behavior", "test"]


@dataclass(frozen=True, slots=True)
class CorpusGateResult:
    """Outcome of evaluating whether a corpus may be used for a purpose."""

    allowed: bool
    reasons: tuple[str, ...]
    signals: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


def evaluate_corpus_manifest(
    manifest: CorpusManifest,
    *,
    purpose: GatePurpose = "production_behavior",
    computed_fingerprint: str | None = None,
    additional_denied_fingerprints: Sequence[str] = (),
) -> CorpusGateResult:
    """
    Evaluate corpus metadata against Spec v1.0 fail-closed rules.

    Production behavioral evaluation requires ``CorpusRole.EVALUATION``.
    Tests may also allow ``CorpusRole.SMOKE_FIXTURE``.
    ``CorpusRole.TRAINING`` is always rejected.
    """
    reasons: list[str] = []
    denied = frozenset(manifest.denied_training_fingerprints) | frozenset(
        str(item) for item in additional_denied_fingerprints
    )
    signals: dict[str, Any] = {
        "purpose": purpose,
        "role": manifest.role.value,
        "fingerprint": manifest.fingerprint,
        "computed_fingerprint": computed_fingerprint,
        "denied_count": len(denied),
    }

    if purpose == "production_behavior":
        if manifest.role is not CorpusRole.EVALUATION:
            reasons.append(f"role_not_evaluation:{manifest.role.value}")
    elif purpose == "test":
        if manifest.role not in (CorpusRole.EVALUATION, CorpusRole.SMOKE_FIXTURE):
            reasons.append(f"role_not_allowed_for_test:{manifest.role.value}")
    else:
        reasons.append(f"unknown_purpose:{purpose}")

    if not manifest.fingerprint.strip():
        reasons.append("fingerprint_missing")

    if computed_fingerprint is not None:
        if not computed_fingerprint.strip():
            reasons.append("computed_fingerprint_missing")
        elif computed_fingerprint != manifest.fingerprint:
            reasons.append("fingerprint_mismatch")

    if manifest.fingerprint in denied:
        reasons.append("fingerprint_on_training_deny_list")

    allowed = not reasons
    return CorpusGateResult(
        allowed=allowed,
        reasons=tuple(reasons),
        signals=MappingProxyType(signals),
    )


def require_corpus_manifest(
    manifest: CorpusManifest,
    *,
    purpose: GatePurpose = "production_behavior",
    computed_fingerprint: str | None = None,
    additional_denied_fingerprints: Sequence[str] = (),
) -> CorpusGateResult:
    """Evaluate gates and raise ``CorpusGateError`` when not allowed."""
    from aiodoo_validation.corpus.exceptions import CorpusGateError

    result = evaluate_corpus_manifest(
        manifest,
        purpose=purpose,
        computed_fingerprint=computed_fingerprint,
        additional_denied_fingerprints=additional_denied_fingerprints,
    )
    if not result.allowed:
        raise CorpusGateError(
            f"Corpus gate rejected corpus {manifest.corpus_id!r}: {', '.join(result.reasons)}"
        )
    return result


__all__ = [
    "CorpusGateResult",
    "GatePurpose",
    "evaluate_corpus_manifest",
    "require_corpus_manifest",
]

"""Placeholder fingerprint providers (Phase 2)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

from aiodoo_validation.domain.artifacts import ArtifactFingerprint
from aiodoo_validation.domain.enums import ArtifactResolutionErrorCode, FingerprintPolicy
from aiodoo_validation.domain.resolution import ArtifactResolutionError


class FingerprintProviderPort(Protocol):
    """Compute and optionally verify artifact fingerprints."""

    def digest_for_path(self, path: Path) -> ArtifactFingerprint: ...

    def verify_expected(
        self,
        *,
        expected: str | None,
        actual: ArtifactFingerprint,
        policy: FingerprintPolicy,
        field: str,
    ) -> tuple[ArtifactResolutionError | None, str | None]:
        """
        Verify expected fingerprint against actual.

        Returns (error, warning). Only one may be set.
        """


class PlaceholderFingerprintProvider:
    """Deterministic placeholder digests — no content hashing in Phase 2."""

    def digest_for_path(self, path: Path) -> ArtifactFingerprint:
        normalized = str(path.resolve())
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
        return ArtifactFingerprint(value=f"placeholder:{digest}", placeholder=True)

    def verify_expected(
        self,
        *,
        expected: str | None,
        actual: ArtifactFingerprint,
        policy: FingerprintPolicy,
        field: str,
    ) -> tuple[ArtifactResolutionError | None, str | None]:
        if policy is FingerprintPolicy.OFF or not expected:
            return None, None
        if expected == actual.value:
            return None, None
        message = f"Fingerprint mismatch for {field}: expected {expected!r}, got {actual.value!r}."
        if policy is FingerprintPolicy.STRICT:
            return (
                ArtifactResolutionError(
                    code=ArtifactResolutionErrorCode.FINGERPRINT_MISMATCH,
                    message=message,
                    field=field,
                ),
                None,
            )
        return None, message

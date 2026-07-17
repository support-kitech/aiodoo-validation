"""Public ValidationService facade (Phase 11)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.domain.result import ValidationRunResult
from aiodoo_validation.engine import ValidationEngine


@dataclass(frozen=True, slots=True)
class ValidationService:
    """
    Stable integration entry point for ecosystem repositories.

    Delegates to ``ValidationEngine`` without adding validation logic.
    """

    _engine: ValidationEngine

    @classmethod
    def create_default(cls) -> ValidationService:
        """Create a service backed by the filesystem artifact resolver."""
        return cls(_engine=ValidationEngine.with_filesystem())

    @classmethod
    def create_with_stubs(cls) -> ValidationService:
        """Create a service backed by stub pipeline components (testing)."""
        return cls(_engine=ValidationEngine.with_stubs())

    def validate(self, request: ValidationRequest) -> ValidationRunResult:
        """Execute the validation lifecycle and return the final result."""
        return self._engine.run(request)

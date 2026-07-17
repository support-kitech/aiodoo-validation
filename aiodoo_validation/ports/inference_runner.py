"""Inference runner port."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.inference import (
    GenerationRequest,
    InferenceGenerationOutcome,
    InferenceInitializationOutcome,
)


class InferenceRunnerPort(Protocol):
    """Load model artifacts and execute generation (Phase 3+)."""

    def initialize(self, context: RunContext) -> InferenceInitializationOutcome: ...

    def generate(
        self,
        context: RunContext,
        request: GenerationRequest,
    ) -> InferenceGenerationOutcome: ...

    def shutdown(self, context: RunContext) -> None: ...

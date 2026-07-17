"""Model runtime port — infrastructure boundary for inference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.inference import GenerationRequest, InferenceResult
from aiodoo_validation.inference.paths import ArtifactLoadPaths


@dataclass(frozen=True, slots=True)
class LoadedModelHandle:
    """Opaque handle to a loaded model runtime (never exposed above inference layer)."""

    token: str
    model_identifier: str
    adapter_type: str


class ModelRuntimePort(Protocol):
    """Load artifacts and execute generation without leaking framework types."""

    runtime_name: str

    def load(self, bundle: ArtifactBundle, paths: ArtifactLoadPaths) -> LoadedModelHandle: ...

    def generate(
        self,
        handle: LoadedModelHandle,
        request: GenerationRequest,
    ) -> InferenceResult: ...

    def unload(self, handle: LoadedModelHandle) -> None: ...

    def verify(self, handle: LoadedModelHandle) -> None: ...

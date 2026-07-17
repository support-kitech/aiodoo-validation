"""Mock model runtime for CPU-only tests (Phase 3)."""

from __future__ import annotations

import hashlib
import time
from uuid import uuid4

from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.inference import (
    GenerationMetadata,
    GenerationRequest,
    InferenceResult,
)
from aiodoo_validation.inference.paths import ArtifactLoadPaths
from aiodoo_validation.inference.runtime.port import LoadedModelHandle


class MockModelRuntime:
    """Deterministic mock runtime — no GPU, downloads, or ML frameworks."""

    runtime_name = "mock"

    def __init__(self) -> None:
        self._loaded: dict[str, LoadedModelHandle] = {}

    def load(self, bundle: ArtifactBundle, paths: ArtifactLoadPaths) -> LoadedModelHandle:
        del paths
        token = f"mock-{uuid4().hex[:12]}"
        model_identifier = str(bundle.base_model.metadata.get("identifier", "qwen3-8b"))
        adapter_type = str(bundle.adapter.metadata.get("adapter_type", "coding"))
        handle = LoadedModelHandle(
            token=token,
            model_identifier=model_identifier,
            adapter_type=adapter_type,
        )
        self._loaded[token] = handle
        return handle

    def verify(self, handle: LoadedModelHandle) -> None:
        if handle.token not in self._loaded:
            raise RuntimeError("Mock model handle is not loaded.")

    def generate(self, handle: LoadedModelHandle, request: GenerationRequest) -> InferenceResult:
        self.verify(handle)
        started = time.perf_counter()
        seed = request.seed if request.seed is not None else 0
        digest = hashlib.sha256(f"{seed}:{request.prompt}".encode()).hexdigest()[:8]
        words = max(1, min(request.max_tokens // 4, 32))
        generated = " ".join(f"token{i}" for i in range(words))
        generated_text = f"[mock:{digest}] {generated}"
        prompt_tokens = max(1, len(request.prompt.split()))
        completion_tokens = len(generated_text.split())
        latency_ms = int((time.perf_counter() - started) * 1000)
        return InferenceResult(
            generated_text=generated_text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=max(latency_ms, 1),
            memory_usage_mb=128.0,
            metadata=GenerationMetadata(
                model_identifier=handle.model_identifier,
                adapter_type=handle.adapter_type,
                seed=request.seed,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                runtime=self.runtime_name,
            ),
        )

    def unload(self, handle: LoadedModelHandle) -> None:
        self._loaded.pop(handle.token, None)

"""Qwen model runtime — optional HuggingFace / PEFT backend (Phase 3)."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.enums import InferenceErrorCode
from aiodoo_validation.domain.inference import (
    GenerationMetadata,
    GenerationRequest,
    InferenceError,
    InferenceResult,
)
from aiodoo_validation.inference.paths import ArtifactLoadPaths
from aiodoo_validation.inference.runtime.port import LoadedModelHandle


class QwenModelRuntime:
    """
    Qwen3-8B + coding adapter runtime.

    Framework imports are lazy and confined to this module. When torch/transformers
    are unavailable the load path returns structured errors instead of crashing.
    """

    runtime_name = "qwen_hf"

    def __init__(self) -> None:
        self._loaded: dict[str, tuple[Any, Any]] = {}
        self._meta: dict[str, LoadedModelHandle] = {}

    def load(self, bundle: ArtifactBundle, paths: ArtifactLoadPaths) -> LoadedModelHandle:
        try:
            import torch
            from peft import PeftModel
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise InferenceError(
                code=InferenceErrorCode.UNSUPPORTED_CONFIG,
                message=f"Inference runtime dependencies are not installed: {exc}",
            ) from exc

        token = f"qwen-{uuid4().hex[:12]}"
        try:
            tokenizer = AutoTokenizer.from_pretrained(str(paths.base_model), trust_remote_code=True)
            base_model = AutoModelForCausalLM.from_pretrained(
                str(paths.base_model),
                trust_remote_code=True,
                torch_dtype=torch.float32,
                device_map="cpu",
            )
            adapted = PeftModel.from_pretrained(base_model, str(paths.adapter))
            adapted.eval()
        except RuntimeError as exc:
            message = str(exc)
            if "out of memory" in message.lower() or "oom" in message.lower():
                raise InferenceError(
                    code=InferenceErrorCode.OOM,
                    message=message,
                ) from exc
            raise InferenceError(
                code=InferenceErrorCode.MODEL_LOAD_FAILURE,
                message=message,
            ) from exc
        except OSError as exc:
            raise InferenceError(
                code=InferenceErrorCode.MODEL_LOAD_FAILURE,
                message=str(exc),
            ) from exc
        except Exception as exc:  # noqa: BLE001 — adapter failures must be structured
            raise InferenceError(
                code=InferenceErrorCode.ADAPTER_LOAD_FAILURE,
                message=str(exc),
            ) from exc

        model_identifier = str(bundle.base_model.metadata.get("identifier", "qwen3-8b"))
        adapter_type = str(bundle.adapter.metadata.get("adapter_type", "coding"))
        handle = LoadedModelHandle(
            token=token,
            model_identifier=model_identifier,
            adapter_type=adapter_type,
        )
        self._loaded[token] = (tokenizer, adapted)
        self._meta[token] = handle
        return handle

    def verify(self, handle: LoadedModelHandle) -> None:
        if handle.token not in self._loaded:
            raise InferenceError(
                code=InferenceErrorCode.NOT_INITIALIZED,
                message="Model runtime is not loaded.",
            )

    def generate(self, handle: LoadedModelHandle, request: GenerationRequest) -> InferenceResult:
        self.verify(handle)
        try:
            import torch
        except ImportError as exc:
            raise InferenceError(
                code=InferenceErrorCode.UNSUPPORTED_CONFIG,
                message=str(exc),
            ) from exc

        payload = self._loaded[handle.token]
        tokenizer: Any = payload[0]
        model: Any = payload[1]
        started = time.perf_counter()
        try:
            if request.seed is not None:
                torch.manual_seed(request.seed)

            encoded = tokenizer(request.prompt, return_tensors="pt")
            input_ids = encoded["input_ids"]
            attention_mask = encoded.get("attention_mask")
            prompt_tokens = int(input_ids.shape[-1])

            with torch.no_grad():
                output = model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=request.max_tokens,
                    temperature=request.temperature,
                    do_sample=request.temperature > 0,
                )

            generated_ids = output[0][prompt_tokens:]
            generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
            completion_tokens = int(generated_ids.shape[-1])
        except RuntimeError as exc:
            message = str(exc)
            if "out of memory" in message.lower() or "oom" in message.lower():
                raise InferenceError(
                    code=InferenceErrorCode.OOM,
                    message=message,
                ) from exc
            raise InferenceError(
                code=InferenceErrorCode.GENERATION_FAILURE,
                message=message,
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise InferenceError(
                code=InferenceErrorCode.GENERATION_FAILURE,
                message=str(exc),
            ) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        return InferenceResult(
            generated_text=generated_text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=max(latency_ms, 1),
            memory_usage_mb=None,
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
        payload = self._loaded.pop(handle.token, None)
        self._meta.pop(handle.token, None)
        if payload is not None:
            try:
                import gc

                import torch

                model: Any = payload[1]
                del model
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()
            except ImportError:
                pass

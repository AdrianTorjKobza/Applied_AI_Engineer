"""Ollama adapter — uses the OpenAI-compatible /api/chat endpoint."""

from __future__ import annotations

import time
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from llm_eval.models import ModelConfig, ModelResponse


class OllamaAdapter:
    """Thin async client for Ollama's chat completion API."""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
        )

    async def __aenter__(self) -> OllamaAdapter:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _chat(
        self,
        messages: list[dict[str, str]],
        extra_params: dict[str, Any],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.name,
            "messages": messages,
            "stream": False,
            **extra_params,
        }
        resp = await self._client.post("/api/chat", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def generate(
        self,
        prompt_id: str,
        user: str,
        system: str | None = None,
    ) -> ModelResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        t0 = time.perf_counter()
        try:
            data = await self._chat(messages, self.config.extra_params)
            latency_ms = (time.perf_counter() - t0) * 1000

            output: str = data.get("message", {}).get("content", "")
            data.get("eval_count", {}) or {}
            prompt_eval: int | None = data.get("prompt_eval_count")
            completion_eval: int | None = data.get("eval_count")

            return ModelResponse(
                model_name=self.config.display_name,
                prompt_id=prompt_id,
                output=output,
                latency_ms=round(latency_ms, 1),
                tokens_prompt=prompt_eval,
                tokens_completion=completion_eval,
            )
        except Exception as exc:  # noqa: BLE001
            latency_ms = (time.perf_counter() - t0) * 1000
            return ModelResponse(
                model_name=self.config.display_name,
                prompt_id=prompt_id,
                output="",
                latency_ms=round(latency_ms, 1),
                error=str(exc),
            )

    async def list_models(self) -> list[str]:
        """Return names of models currently pulled in Ollama."""
        resp = await self._client.get("/api/tags")
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]

    async def close(self) -> None:
        await self._client.aclose()

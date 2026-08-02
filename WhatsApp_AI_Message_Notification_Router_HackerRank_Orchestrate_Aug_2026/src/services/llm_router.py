"""Async Ollama VLM integration service with retry resilience and detailed error logging."""

import asyncio
import base64
import json
import logging
from typing import Any
import httpx
from src.config import settings
from src.domain.exceptions import LLMInferenceError
from src.domain.models import LLMPrediction
from src.prompts import ROUTER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class OllamaRouterService:
    """Sends combined prompt, context, and images to local Ollama daemon."""

    def __init__(self) -> None:
        self.endpoint = f"{settings.ollama_base_url}/api/generate"

    @staticmethod
    def _encode_image_to_base64(media_id: str) -> str:
        """Encodes an image file from dataset/media/images/ to clean base64 string."""
        if not media_id:
            return ""

        for ext in (".jpg", ".png", ".jpeg", ".webp"):
            img_path = settings.images_dir / f"{media_id}{ext}"
            if img_path.exists():
                try:
                    if img_path.stat().st_size == 0:
                        logger.warning(
                            "Image file %s is empty (0 bytes). Skipping.",
                            img_path.name,
                        )
                        return ""
                    with open(img_path, "rb") as image_file:
                        return base64.b64encode(image_file.read()).decode("utf-8")
                except OSError as exc:
                    logger.warning(
                        "Failed reading image file %s: %s",
                        img_path.name,
                        exc,
                    )
                    return ""

        logger.warning(
            "Image media file not found for ID: %s inside %s",
            media_id,
            settings.images_dir,
        )
        return ""

    @staticmethod
    def _parse_confidence_safe(val: Any) -> float:
        """Safely parses float confidence from LLM response strings or numbers.

        Args:
            val: Raw confidence input (e.g., 0.85, "0.85", "85%").

        Returns:
            float: Normalized float confidence between 0.0 and 1.0.
        """
        try:
            if isinstance(val, (int, float)):
                score = float(val)
            elif isinstance(val, str):
                cleaned = val.replace("%", "").strip()
                score = float(cleaned)
                if score > 1.0:
                    score /= 100.0  # Handle percentage strings like "85"
            else:
                score = settings.confidence_default_llm

            # Clamp LLM self-reported score within sensible baseline range
            return max(0.10, min(0.95, score))
        except (ValueError, TypeError):
            logger.debug(
                "Unparseable LLM confidence '%s'. Using default %.2f",
                val,
                settings.confidence_default_llm,
            )
            return settings.confidence_default_llm

    async def predict_async(
        self,
        message_text: str,
        media_type: str,
        media_id: str,
        context_str: str,
        evidence_ids: str,
    ) -> LLMPrediction:
        """Dispatches request asynchronously to local Ollama daemon with transient retry logic.

        Args:
            message_text: Plain text content or voice note transcription.
            media_type: Type of attached media ('image', 'voice', or empty).
            media_id: Identifier of attached media file.
            context_str: Formatted context string.
            evidence_ids: Semicolon-separated historical message IDs.

        Returns:
            LLMPrediction: Parsed prediction or safe heuristic fallback.
        """
        images: list[str] = []
        if media_type == "image" and media_id:
            b64_img = self._encode_image_to_base64(media_id)
            if b64_img:
                images.append(b64_img)

        prompt = ROUTER_SYSTEM_PROMPT.format(
            context_str=context_str,
            evidence_ids=evidence_ids,
            message_text=message_text,
        )

        payload = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }
        if images:
            payload["images"] = images

        for attempt in range(1, settings.ollama_max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
                    response = await client.post(self.endpoint, json=payload)
                    response.raise_for_status()
                    data = response.json()

                    raw_json = json.loads(data.get("response", "{}"))
                    raw_conf = self._parse_confidence_safe(
                        raw_json.get("confidence", settings.confidence_default_llm)
                    )

                    return LLMPrediction(
                        action=raw_json.get("action", "digest"),
                        message_type=raw_json.get("message_type", "unknown"),
                        reason=raw_json.get("reason", "Automated model response"),
                        confidence=raw_conf,
                    )

            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                error_body = exc.response.text

                if status_code == 400 and images:
                    logger.warning(
                        "Ollama rejected image payload (HTTP 400). Retrying text-only inference."
                    )
                    payload.pop("images", None)
                    continue

                if status_code == 404:
                    logger.error(
                        "Ollama HTTP 404 Not Found. Target endpoint or model is missing.\n"
                        "Requested Model: '%s' | Ollama Response Body: %s",
                        settings.ollama_model,
                        error_body,
                    )
                    break

                logger.warning(
                    "LLM HTTP Status Error (Attempt %d/%d): Status %d - %s",
                    attempt,
                    settings.ollama_max_retries,
                    status_code,
                    error_body,
                )

                if status_code < 500:
                    break

            except (httpx.RequestError, json.JSONDecodeError) as exc:
                logger.warning(
                    "LLM Transient Request Error (Attempt %d/%d): %s",
                    attempt,
                    settings.ollama_max_retries,
                    exc,
                )

            if attempt < settings.ollama_max_retries:
                await asyncio.sleep(
                    settings.ollama_retry_backoff * (2 ** (attempt - 1))
                )

        logger.error(
            "LLM API execution failed after %d attempts. Falling back to default 'digest'.",
            settings.ollama_max_retries,
        )
        return LLMPrediction(
            action="digest",
            message_type="unknown",
            reason="Defaulting to digest due to LLM processing or availability error.",
            confidence=settings.confidence_min_clamp,
        )
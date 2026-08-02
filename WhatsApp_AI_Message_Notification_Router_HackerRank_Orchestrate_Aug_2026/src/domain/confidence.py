"""Domain service for calibrating multi-signal classification confidence."""

import logging
from src.config import settings

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Calculates composite confidence scores using LLM certainty and domain signals."""

    @classmethod
    def calibrate(
        self,
        raw_llm_confidence: float,
        evidence_ids: str,
        message_text: str,
        is_deterministic_override: bool = False,
    ) -> float:
        """Computes calibrated confidence bounded by configured clamp limits.

        Args:
            raw_llm_confidence: Self-reported confidence score from the LLM (0.0 to 1.0).
            evidence_ids: Semicolon-separated evidence message IDs or 'none'.
            message_text: Text content checked for media degradation markers.
            is_deterministic_override: Flag indicating if a policy override was triggered.

        Returns:
            float: Calibrated confidence score rounded to 2 decimal places.
        """
        # 1. Deterministic rules (Quiet hours, Mute, Scam safety) have highest certainty
        if is_deterministic_override:
            logger.debug(
                "Policy override active. Assigning deterministic ceiling: %.2f",
                settings.confidence_override_score,
            )
            return settings.confidence_override_score

        score = raw_llm_confidence

        # 2. Apply positive boost if decision is grounded in historical evidence
        if evidence_ids and evidence_ids.strip().lower() != "none":
            logger.debug(
                "Applying evidence grounding boost (+%.2f) for evidence: %s",
                settings.confidence_evidence_boost,
                evidence_ids,
            )
            score += settings.confidence_evidence_boost

        # 3. Apply penalty if voice transcription or image loading degraded
        if (
            "[Voice Note Audio Unreadable]" in message_text
            or "[Voice Note Audio File Missing]" in message_text
        ):
            logger.debug(
                "Applying media degradation penalty (-%.2f) due to unreadable audio",
                settings.confidence_media_penalty,
            )
            score -= settings.confidence_media_penalty

        # 4. Clamp score within configured domain boundaries
        clamped_score = max(
            settings.confidence_min_clamp,
            min(settings.confidence_max_clamp, score),
        )

        return round(clamped_score, 2)
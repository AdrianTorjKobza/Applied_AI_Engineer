"""Deterministic Policy Engine enforcing business rules and confidence calibration."""

import logging
from datetime import datetime
from src.domain.confidence import ConfidenceScorer
from src.domain.models import GroupMemberMetadata, LLMPrediction, UserMetadata

logger = logging.getLogger(__name__)


class PolicyEngine:
    """Evaluates and applies deterministic business logic overrides on top of LLM outputs."""

    @staticmethod
    def apply_overrides(
        prediction: LLMPrediction,
        created_at_str: str,
        user_meta: UserMetadata,
        evidence_ids: str = "none",
        message_text: str = "",
        group_meta: GroupMemberMetadata | None = None,
    ) -> LLMPrediction:
        """Applies strict priority overrides and calibrates confidence.

        Args:
            prediction: Raw LLM prediction.
            created_at_str: Message creation timestamp string.
            user_meta: Receiving user metadata.
            evidence_ids: Historical evidence IDs string.
            message_text: Full processed message text.
            group_meta: Optional group metadata for the user.

        Returns:
            LLMPrediction: Calibrated prediction following override rules.
        """
        action = prediction.action.lower()
        msg_type = prediction.message_type.lower()
        reason = prediction.reason
        raw_confidence = prediction.confidence
        is_overridden = False

        # Rule 1: Safety & Scam Override -> Always Mute
        if msg_type in ("scam", "spam"):
            logger.debug("Triggered safety override for message type: %s", msg_type)
            action = "mute"
            reason = f"[Safety Override] {reason}"
            is_overridden = True

        # Rule 2: Group Mute Override -> Downgrade notify to digest
        elif group_meta and group_meta.is_muted and action == "notify":
            logger.debug(
                "Triggered muted group override for user %s",
                user_meta.user_id,
            )
            action = "digest"
            reason = f"[Muted Group Override] {reason}"
            is_overridden = True

        # Rule 3: Quiet Hours Override -> Downgrade non-urgent notify to digest
        elif (
            user_meta
            and user_meta.quiet_hours_start is not None
            and user_meta.quiet_hours_end is not None
        ):
            if PolicyEngine._is_in_quiet_hours(
                created_at_str,
                user_meta.quiet_hours_start,
                user_meta.quiet_hours_end,
            ):
                if action == "notify" and msg_type != "urgent":
                    logger.debug(
                        "Triggered quiet hours override for user %s",
                        user_meta.user_id,
                    )
                    action = "digest"
                    reason = f"[Quiet Hours Override] {reason}"
                    is_overridden = True

        # Calibrate composite confidence score
        calibrated_confidence = ConfidenceScorer.calibrate(
            raw_llm_confidence=raw_confidence,
            evidence_ids=evidence_ids,
            message_text=message_text,
            is_deterministic_override=is_overridden,
        )

        return LLMPrediction(
            action=action,
            message_type=msg_type,
            reason=reason,
            confidence=calibrated_confidence,
        )

    @staticmethod
    def _is_in_quiet_hours(timestamp_str: str, start_hour: int, end_hour: int) -> bool:
        """Determines if timestamp falls within start and end hours."""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            hour = dt.hour
        except ValueError as exc:
            logger.warning(
                "Timestamp parsing failed for string '%s': %s",
                timestamp_str,
                exc,
            )
            return False

        if start_hour <= end_hour:
            return start_hour <= hour < end_hour
        return hour >= start_hour or hour < end_hour
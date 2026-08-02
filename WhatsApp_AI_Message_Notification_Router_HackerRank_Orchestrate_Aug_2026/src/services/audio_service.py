"""Audio transcription service using faster-whisper."""

import logging
from faster_whisper import WhisperModel
from src.config import settings
from src.domain.exceptions import MediaProcessingError

logger = logging.getLogger(__name__)


class AudioService:
    """Manages audio loading and speech-to-text processing from dataset/media/audio/."""

    def __init__(self) -> None:
        self._model: WhisperModel | None = None

    def _get_model(self) -> WhisperModel:
        """Lazy loader for Whisper model to save memory until required."""
        if self._model is None:
            logger.info("Initializing Whisper model (%s)...", settings.whisper_model_size)
            try:
                self._model = WhisperModel(
                    settings.whisper_model_size,
                    device=settings.whisper_device,
                    compute_type=settings.whisper_compute_type,
                )
            except Exception as exc:
                logger.error("Failed to initialize Whisper model: %s", exc)
                raise MediaProcessingError("Whisper initialization failed.") from exc
        return self._model

    def transcribe(self, media_id: str) -> str:
        """Transcribes audio file from the dedicated audio directory dataset/media/audio/.

        Args:
            media_id: Identifier of the audio file.

        Returns:
            str: Transcribed text or descriptive fallback string.
        """
        if not media_id:
            return ""

        for ext in (".ogg", ".wav", ".mp3", ".m4a"):
            audio_path = settings.audio_dir / f"{media_id}{ext}"
            if audio_path.exists():
                try:
                    model = self._get_model()
                    segments, _ = model.transcribe(str(audio_path), beam_size=1)
                    text = " ".join(segment.text for segment in segments).strip()
                    logger.debug("Successfully transcribed audio file: %s", audio_path.name)
                    return f"[Voice Note Transcription]: {text}"
                except Exception as exc:
                    logger.warning("Audio transcription error for %s: %s", audio_path.name, exc)
                    return "[Voice Note Audio Unreadable]"

        logger.warning("Audio media file not found for ID: %s inside %s", media_id, settings.audio_dir)
        return "[Voice Note Audio File Missing]"
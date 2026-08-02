"""Centralized application configuration managed via Pydantic Settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or defaults.

    Attributes:
        base_dir: Root directory of the project.
        dataset_dir: Path to input datasets.
        media_dir: Path to media root directory.
        images_dir: Path to image media files.
        audio_dir: Path to audio media files.
        chroma_dir: Path to ChromaDB persistent storage.
        ollama_base_url: HTTP base URL for local Ollama daemon.
        ollama_model: Local multimodal model tag.
        ollama_timeout: Timeout in seconds for HTTP requests to Ollama.
        ollama_max_retries: Maximum retry attempts for transient LLM errors.
        ollama_retry_backoff: Initial backoff delay in seconds between retries.
        whisper_model_size: Size of faster-whisper model.
        whisper_device: Compute device for Whisper ('cpu' or 'cuda').
        whisper_compute_type: Quantization type for Whisper.
        concurrent_requests: Max concurrent LLM requests.
        log_level: Logging verbosity level.
        confidence_default_llm: Default fallback LLM confidence if unparseable.
        confidence_evidence_boost: Boost applied when historical evidence is present.
        confidence_media_penalty: Penalty applied when media is unreadable.
        confidence_override_score: High deterministic confidence for rule overrides.
        confidence_min_clamp: Minimum allowable confidence boundary.
        confidence_max_clamp: Maximum allowable confidence boundary.
    """

    model_config = SettingsConfigDict(
        env_prefix="ROUTER_",
        env_file=".env",
        extra="ignore",
    )

    base_dir: Path = Path(__file__).resolve().parent.parent
    dataset_dir: Path = base_dir / "dataset"
    media_dir: Path = dataset_dir / "media"
    images_dir: Path = dataset_dir / "media" / "images"
    audio_dir: Path = dataset_dir / "media" / "audio"
    chroma_dir: Path = base_dir / "data_store"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5vl:7b"
    ollama_timeout: float = 120.0
    ollama_max_retries: int = 5
    ollama_retry_backoff: float = 2.0

    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    concurrent_requests: int = 2
    log_level: str = "INFO"

    # Dynamic Confidence Calibration Configuration
    confidence_default_llm: float = 0.75
    confidence_evidence_boost: float = 0.10
    confidence_media_penalty: float = 0.15
    confidence_override_score: float = 0.98
    confidence_min_clamp: float = 0.30
    confidence_max_clamp: float = 0.99

    @property
    def messages_csv_path(self) -> Path:
        """Returns the absolute path to the target messages.csv file."""
        return self.dataset_dir / "messages.csv"

    @property
    def output_csv_path(self) -> Path:
        """Returns the absolute path to the target output.csv file."""
        return self.dataset_dir / "output.csv"


settings = Settings()
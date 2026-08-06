"""
Centralized configuration for local-first execution.
Manages hardware compute flags, Ollama connection endpoints,
model selections, and filesystem paths.
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Runtime configuration for the Local AI Meeting Assistant."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Ollama Inference Settings ---
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for the local Ollama API service.",
    )
    llm_model: str = Field(
        default="llama3.1:8b-instruct-q8_0",
        description="Target Ollama model tag. Q8_0 recommended for 32GB RAM machines.",
    )
    llm_temperature: float = Field(
        default=0.1,
        description="Low temperature for deterministic schema and action item extraction.",
    )

    # --- WhisperX Audio & Diarization Settings ---
    whisper_model_size: str = Field(
        default="medium",
        description="Whisper model size ('small', 'medium', 'large-v3'). 'medium' is optimal for accuracy/speed on Intel CPU.",
    )
    whisper_device: str = Field(
        default="cpu",
        description="Execution device ('cpu' or 'cuda').",
    )
    whisper_compute_type: str = Field(
        default="int8",
        description="CTranslate2 compute type. Use 'int8' for fast Intel CPU instruction set execution.",
    )

    # --- Map-Reduce Chunking Constraints ---
    chunk_token_limit: int = Field(
        default=2800,
        description="Maximum token size per chunk for the Map-Reduce summarization pipeline.",
    )

    # --- Directory Paths ---
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent,
        description="Root directory of the project.",
    )
    data_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "data",
        description="Root directory for application data artifacts.",
    )
    input_audio_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "input_audio",
        description="Directory for incoming raw .wav files.",
    )
    transcripts_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "transcripts",
        description="Directory for saved speaker-diarized transcript JSON files.",
    )
    outputs_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "outputs",
        description="Directory for generated Markdown (.md) and Email draft (.eml) files.",
    )

    def ensure_directories(self) -> None:
        """Create required data folders on disk if they do not exist."""
        for path_field in [
            self.data_dir,
            self.input_audio_dir,
            self.transcripts_dir,
            self.outputs_dir,
        ]:
            path_field.mkdir(parents=True, exist_ok=True)


# Global singleton instance for easy import across modules
settings = AppSettings()
settings.ensure_directories()
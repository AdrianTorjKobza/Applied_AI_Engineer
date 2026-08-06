"""
Provides validation and utility helper functions for audio file processing.
"""

import os
from pathlib import Path
from typing import Set


SUPPORTED_AUDIO_EXTENSIONS: Set[str] = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}


def validate_audio_file(file_path: str | Path) -> Path:
    """
    Validates that the provided file exists, is a regular file, and has a supported
    audio extension.

    Args:
        file_path: Absolute or relative path to the source audio file.

    Returns:
        Path: Resolved absolute Path object if valid.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is not supported.
    """
    path = Path(file_path).resolve()

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Audio file not found at: {path}")

    if path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
        raise ValueError(
            f"Unsupported audio format '{path.suffix}'. "
            f"Supported extensions: {', '.join(sorted(SUPPORTED_AUDIO_EXTENSIONS))}"
        )

    return path


def format_timestamp(seconds: float) -> str:
    """
    Converts raw seconds into HH:MM:SS format for readable console output.
    """
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
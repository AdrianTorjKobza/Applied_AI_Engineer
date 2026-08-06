"""
Wraps WhisperX and Pyannote to perform speech-to-text transcription,
word-level timestamp alignment, and speaker diarization locally.
"""

import gc
import os
from typing import List, Optional, Tuple
import torch
import whisperx

from config.settings import settings
from src.ingestion.audio_utils import format_timestamp, validate_audio_file
from src.llm.schemas import TranscriptTurn
from whisperx.diarize import DiarizationPipeline


class DiarizationEngine:
    """
    Handles local transcription and speaker diarization using WhisperX.
    Includes explicit memory management to clear PyTorch models from RAM
    after execution.
    """

    def __init__(self, hf_token: Optional[str] = None):
        """
        Args:
            hf_token: HuggingFace read token required for Pyannote gated models.
                      Defaults to HF_TOKEN environment variable if not passed.
        """
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        
        if not self.hf_token:
            raise ValueError(
                "A Hugging Face access token is required for Pyannote speaker diarization. "
                "Set the HF_TOKEN environment variable or pass it to DiarizationEngine."
            )

        self.device = settings.whisper_device
        self.compute_type = settings.whisper_compute_type
        self.model_size = settings.whisper_model_size

    def transcribe_and_diarize(
        self,
        audio_path: str,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
        batch_size: int = 8,
    ) -> Tuple[List[TranscriptTurn], str]:
        """
        Executes the full WhisperX pipeline: Transcription -> Alignment -> Diarization.

        Args:
            audio_path: Path to input audio file.
            min_speakers: Optional hint for minimum speakers in the meeting.
            max_speakers: Optional hint for maximum speakers in the meeting.
            batch_size: Transcription batch size (8 is optimal for 32GB system RAM).

        Returns:
            Tuple[List[TranscriptTurn], str]:
                - List of structured Pydantic TranscriptTurn models.
                - Formatted plain-text transcript string for summarization.
        """
        valid_path = validate_audio_file(audio_path)
        print(f"[Ingestion] Loading audio: {valid_path.name}")
        audio = whisperx.load_audio(str(valid_path))

        # 1. Transcribe with faster-whisper
        print(f"[Ingestion] Running Whisper ({self.model_size}) on {self.device} [{self.compute_type}]...")
        model = whisperx.load_model(
            self.model_size,
            self.device,
            compute_type=self.compute_type,
        )
        result = model.transcribe(audio, batch_size=batch_size)
        detected_language = result.get("language", "en")
        print(f"[Ingestion] Transcription finished. Detected language: {detected_language}")

        # Clean up transcription model from RAM immediately
        del model
        self._clear_memory()

        # 2. Align timestamps to word-level
        print("[Ingestion] Aligning word-level timestamps...")
        align_model, metadata = whisperx.load_align_model(
            language_code=detected_language,
            device=self.device,
        )
        result = whisperx.align(
            result["segments"],
            align_model,
            metadata,
            audio,
            self.device,
            return_char_alignments=False,
        )

        # Clean up alignment model from RAM
        del align_model
        self._clear_memory()

        # 3. Speaker Diarization via Pyannote
        print("[Ingestion] Performing speaker diarization...")
        diarize_pipeline = DiarizationPipeline(
            token=self.hf_token,
            device=self.device,
        )
        diarize_segments = diarize_pipeline(
            audio,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
        )

        # 4. Assign speakers to words/segments
        result = whisperx.assign_word_speakers(diarize_segments, result)

        # Clean up diarization pipeline from RAM
        del diarize_pipeline
        self._clear_memory()

        # 5. Build structured Pydantic turns and plain text transcript
        turns, plain_text = self._format_results(result["segments"])
        print(f"[Ingestion] Success! Processed {len(turns)} diarized speaker turns.")
        return turns, plain_text

    @staticmethod
    def _clear_memory() -> None:
        """Force garbage collection to reclaim system RAM before LLM execution."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @staticmethod
    def _format_results(segments: list) -> Tuple[List[TranscriptTurn], str]:
        """
        Parses raw WhisperX segments into structured Pydantic models and
        a clean plain-text string for LLM chunking.
        """
        turns: List[TranscriptTurn] = []
        text_blocks: List[str] = []

        for seg in segments:
            speaker = seg.get("speaker", "UNKNOWN")
            start = seg.get("start", 0.0)
            end = seg.get("end", 0.0)
            text = seg.get("text", "").strip()

            if not text:
                continue

            turn = TranscriptTurn(
                speaker=speaker,
                start_time=start,
                end_time=end,
                text=text,
            )
            turns.append(turn)

            time_label = f"[{format_timestamp(start)} - {format_timestamp(end)}]"
            text_blocks.append(f"{speaker} {time_label}: {text}")

        formatted_transcript = "\n".join(text_blocks)
        return turns, formatted_transcript
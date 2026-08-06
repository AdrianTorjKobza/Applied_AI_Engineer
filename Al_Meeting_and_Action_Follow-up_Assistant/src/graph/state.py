"""
Defines the LangGraph TypedDict state that flows through transcription,
Map-Reduce summarization, Markdown export, and HITL email drafting.
"""

import operator
from typing import Annotated, List, Optional, TypedDict
from src.llm.schemas import EmailDraft, MeetingRecord, TranscriptTurn


class MeetingState(TypedDict, total=False):
    """
    The shared state container passed across all LangGraph nodes.
    
    Attributes:
        audio_file_path: Absolute path to the source .wav file.
        meeting_title: Human-readable title provided via CLI.
        meeting_timestamp: Formatted string 'YYYYMMDD_HHMM' used for unique filenames.
        
        transcript_turns: Diarized speaker turns from WhisperX/Pyannote.
        formatted_transcript: Plaintext string representation of the full transcript.
        
        chunks: List of text segments split for Map-Reduce processing.
        partial_records: Accumulated partial MeetingRecords from parallel Map nodes.
        final_record: The consolidated, deduplicated MeetingRecord from the Reduce node.
        
        markdown_file_path: Absolute path where the summary .md file was written.
        
        email_draft: The generated email draft awaiting human approval.
        email_approved: HITL decision flag (True = Approved, False = Rejected, None = Pending).
        email_feedback: Optional textual feedback from the reviewer if edits are needed.
        eml_file_path: Absolute path where the .eml file was written (if approved).
    """

    # --- Input Metadata ---
    audio_file_path: str
    meeting_title: str
    meeting_timestamp: str

    # --- Ingestion & Diarization State ---
    transcript_turns: List[TranscriptTurn]
    formatted_transcript: str

    # --- Map-Reduce Summarization State ---
    chunks: List[str]
    # operator.add allows parallel Map nodes to append their results safely
    partial_records: Annotated[List[MeetingRecord], operator.add]
    final_record: Optional[MeetingRecord]

    # --- Artifact Export State (No HITL) ---
    markdown_file_path: Optional[str]

    # --- HITL & Outbound Email State ---
    email_draft: Optional[EmailDraft]
    email_approved: Optional[bool]
    email_feedback: Optional[str]
    eml_file_path: Optional[str]
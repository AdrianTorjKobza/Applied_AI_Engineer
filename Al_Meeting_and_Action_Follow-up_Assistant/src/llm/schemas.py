"""
Defines domain data schemas for transcript turns, extracted meeting records,
and email drafts using Pydantic v2.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TranscriptTurn(BaseModel):
    """Represents a single speaker turn from the diarization pipeline."""

    speaker: str = Field(
        ...,
        description="The identified speaker label (e.g., 'SPEAKER_00', 'SPEAKER_01').",
    )
    start_time: float = Field(
        ...,
        description="Start timestamp in seconds from the beginning of the audio.",
    )
    end_time: float = Field(
        ...,
        description="End timestamp in seconds from the beginning of the audio.",
    )
    text: str = Field(
        ...,
        description="The transcribed spoken text for this turn.",
    )

    @field_validator("speaker", mode="before")
    @classmethod
    def normalize_speaker(cls, v: str) -> str:
        """Ensure consistent speaker formatting."""
        return v.strip().upper() if isinstance(v, str) else v


class ActionItem(BaseModel):
    """Represents a discrete action item extracted from the meeting."""

    assignee: str = Field(
        default="Unassigned",
        description="The speaker or team member responsible for the action item. Default to 'Unassigned' if unclear.",
    )
    task: str = Field(
        ...,
        description="Clear, actionable description of the task to be completed.",
    )
    deadline: str = Field(
        default="Not specified",
        description="The due date, deadline, or timeline mentioned. Default to 'Not specified' if none is discussed.",
    )

    @field_validator("assignee", "deadline", mode="before")
    @classmethod
    def handle_empty_strings(cls, v: Optional[str]) -> str:
        """Prevent local LLMs from returning empty strings instead of defaults."""
        if not v or not str(v).strip():
            return "Not specified"
        return str(v).strip()


class MeetingRecord(BaseModel):
    """
    The structured artifact representing the synthesized meeting outcome.
    Maps directly to our target Markdown document schema.
    """

    summary: str = Field(
        ...,
        description="A concise, executive-level synthesis of the primary discussion topics and outcomes.",
    )
    key_decisions: List[str] = Field(
        default_factory=list,
        description="A bulleted list of explicit decisions, approvals, or conclusions agreed upon.",
    )
    actions: List[ActionItem] = Field(
        default_factory=list,
        description="A list of action items, assignees, and deadlines agreed to during the meeting.",
    )
    next_steps: List[str] = Field(
        default_factory=list,
        description="A list of high-level future milestones, scheduled follow-ups, or strategic next steps.",
    )


class EmailDraft(BaseModel):
    """Represents the generated follow-up email content subject to human review."""

    subject: str = Field(
        ...,
        description="A professional and descriptive email subject line including the meeting title.",
    )
    body: str = Field(
        ...,
        description="The full plaintext or markdown email body summarizing decisions and action items.",
    )
    recipients: List[str] = Field(
        default_factory=list,
        description="List of recipient names or speaker identifiers to include on the To line.",
    )
"""
Unit tests for Pydantic v2 domain schemas (TranscriptTurn, ActionItem, MeetingRecord, EmailDraft).
Verifies data normalization and fallback defaults for local LLM extraction.
"""

import pytest
from pydantic import ValidationError
from src.llm.schemas import ActionItem, EmailDraft, MeetingRecord, TranscriptTurn


class TestTranscriptTurnSchema:
    """Tests speaker tag normalization and timestamp validation."""

    def test_speaker_normalization_to_uppercase(self) -> None:
        turn = TranscriptTurn(
            speaker="  speaker_01  ",
            start_time=10.5,
            end_time=15.0,
            text="Let's standardize on SQLite.",
        )
        assert turn.speaker == "SPEAKER_01"

    def test_missing_required_fields_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            # Missing text and end_time
            TranscriptTurn(speaker="SPEAKER_00", start_time=0.0)  # type: ignore[call-arg]


class TestActionItemSchema:
    """Tests field validator fallbacks for empty or whitespace-only LLM strings."""

    @pytest.mark.parametrize(
        "assignee_input, expected_assignee",
        [
            ("", "Not specified"),
            ("   ", "Not specified"),
            (None, "Not specified"),
            ("SPEAKER_02 (Alex)", "SPEAKER_02 (Alex)"),
        ],
    )
    def test_assignee_empty_string_defaults(
        self, assignee_input: str | None, expected_assignee: str
    ) -> None:
        action = ActionItem(
            assignee=assignee_input,  # type: ignore[arg-type]
            task="Prototype the WhisperX pipeline",
            deadline="2026-08-08",
        )
        assert action.assignee == expected_assignee

    @pytest.mark.parametrize(
        "deadline_input, expected_deadline",
        [
            ("", "Not specified"),
            (None, "Not specified"),
            ("End of Q3", "End of Q3"),
        ],
    )
    def test_deadline_empty_string_defaults(
        self, deadline_input: str | None, expected_deadline: str
    ) -> None:
        action = ActionItem(
            assignee="SPEAKER_00",
            task="Draft documentation",
            deadline=deadline_input,  # type: ignore[arg-type]
        )
        assert action.deadline == expected_deadline


class TestMeetingRecordSchema:
    """Tests default factory initialization for list attributes."""

    def test_meeting_record_minimal_instantiation(self) -> None:
        record = MeetingRecord(summary="Executive sync on architecture.")
        assert record.summary == "Executive sync on architecture."
        assert record.key_decisions == []
        assert record.actions == []
        assert record.next_steps == []
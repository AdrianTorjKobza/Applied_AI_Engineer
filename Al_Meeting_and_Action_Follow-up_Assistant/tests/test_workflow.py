"""
Unit and integration tests for LangGraph nodes and workflow checkpointing.
Verifies transcript chunking and tests the HITL interrupt_before edge on write_eml_node.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch
import uuid

from src.graph.nodes import chunk_transcript_node
from src.graph.state import MeetingState
from src.graph.workflow import meeting_graph
from src.llm.schemas import EmailDraft, MeetingRecord


class TestTranscriptChunking:
    """Tests transcript splitting logic against token/word limits."""

    def test_chunking_short_transcript(self) -> None:
        state: MeetingState = {
            "formatted_transcript": (
                "SPEAKER_00 [00:00 - 00:05]: Welcome everyone.\n"
                "SPEAKER_01 [00:06 - 00:10]: Let's get started."
            )
        }
        result = chunk_transcript_node(state)
        chunks = result["chunks"]

        assert len(chunks) == 1
        assert "SPEAKER_00" in chunks[0]
        assert "SPEAKER_01" in chunks[0]

    @patch("src.graph.nodes.settings.chunk_token_limit", 10)
    def test_chunking_long_transcript_splits_cleanly(self) -> None:
        """Simulate a tiny token limit to force multiple chunks along line breaks."""
        lines = [
            "SPEAKER_00 [00:00 - 00:05]: First line with several words.",
            "SPEAKER_01 [00:06 - 00:10]: Second line with several words.",
            "SPEAKER_02 [00:11 - 00:15]: Third line with several words.",
        ]
        state: MeetingState = {"formatted_transcript": "\n".join(lines)}

        result = chunk_transcript_node(state)
        chunks = result["chunks"]

        assert len(chunks) > 1
        assert "First line" in chunks[0]
        assert "Third line" in chunks[-1]


class TestGraphHITLWorkflow:
    """Tests LangGraph MemorySaver interruption and resume behavior."""

    @patch("src.graph.nodes.create_markdown_file")
    @patch("src.graph.nodes.create_eml_draft")
    @patch("src.graph.nodes.llm_client")
    def test_hitl_email_approval_flow(
        self,
        mock_llm: MagicMock,
        mock_create_eml: MagicMock,
        mock_create_md: MagicMock,
        tmp_path: Path,
    ) -> None:
        """
        Verifies that graph execution halts before write_eml_node and only
        executes EML creation after email_approved is explicitly set to True.
        """
        # 1. Setup Mock LLM Outputs
        mock_record = MeetingRecord(
            summary="Architecture test sync summary.",
            key_decisions=["Decision A"],
            actions=[],
            next_steps=[],
        )
        mock_draft = EmailDraft(
            subject="Test Sync Follow-up",
            body="Meeting notes body...",
            recipients=["test@company.internal"],
        )
        mock_llm.summarize_chunk.return_value = mock_record
        mock_llm.generate_email_draft.return_value = mock_draft

        # Mock file export return paths
        mock_create_md.return_value = tmp_path / "summary.md"
        mock_create_eml.return_value = tmp_path / "draft.eml"

        # 2. Define Initial State & Config
        thread_id = str(uuid.uuid4())
        thread_config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
        initial_state: MeetingState = {
            "audio_file_path": "mock/path.wav",
            "meeting_title": "Test Sync",
            "meeting_timestamp": "20260805_1200",
            "formatted_transcript": "SPEAKER_00 [00:00 - 00:05]: Hello world.",
            "partial_records": [],
        }

        # 3. First Invocation: Should halt BEFORE write_eml_node
        meeting_graph.invoke(initial_state, config=thread_config)

        # Verify Markdown file was created automatically, but EML creation was NOT called yet
        mock_create_md.assert_called_once()
        mock_create_eml.assert_not_called()

        # Check graph state at the HITL breakpoint
        state_snapshot = meeting_graph.get_state(thread_config)
        assert state_snapshot.values["email_draft"] == mock_draft
        assert state_snapshot.values["email_approved"] is None
        assert state_snapshot.next == ("write_eml_node",)

        # 4. Simulate Human Approval via update_state
        meeting_graph.update_state(thread_config, {"email_approved": True})

        # 5. Second Invocation: Resume graph to completion
        final_result = meeting_graph.invoke(None, config=thread_config)

        # Verify EML creation was executed upon resuming
        mock_create_eml.assert_called_once()
        assert final_result["eml_file_path"] == str(tmp_path / "draft.eml")
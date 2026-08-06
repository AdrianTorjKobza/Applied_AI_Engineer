"""
Integration tests for Markdown and EML file exporters.
Verifies file generation, filename sanitization, Markdown table structure,
and RFC-compliant unsent MIME email headers.
"""

import email
from email.message import EmailMessage
from pathlib import Path

from src.exporters.email_writer import create_eml_draft
from src.exporters.markdown_writer import create_markdown_file
from src.llm.schemas import ActionItem, EmailDraft, MeetingRecord


def test_markdown_file_creation_and_formatting(tmp_path: Path) -> None:
    """Verifies Markdown summary file naming and structural markdown rendering."""
    record = MeetingRecord(
        summary="Discussed Q3 milestones and database persistence.",
        key_decisions=["Standardize on SQLite for state persistence."],
        actions=[
            ActionItem(
                assignee="SPEAKER_01 (Alex)",
                task="Benchmark WhisperX inference speed",
                deadline="2026-08-10",
            )
        ],
        next_steps=["Review bench results next Tuesday."],
    )
    title = "Q3 Architecture Planning / Review!"
    timestamp = "20260805_1430"

    output_path = create_markdown_file(
        record=record,
        title=title,
        timestamp=timestamp,
        output_dir=tmp_path,
    )

    # Verify sanitized filename (special characters '/' and '!' stripped/replaced)
    assert output_path.exists()
    assert output_path.name == "20260805_1430_Q3_Architecture_Planning___Review.md"

    # Verify Markdown content layout
    content = output_path.read_text(encoding="utf-8")
    assert "# Q3 Architecture Planning / Review!" in content
    assert "## Summary" in content
    assert "Discussed Q3 milestones and database persistence." in content
    assert "| **SPEAKER_01 (Alex)** | Benchmark WhisperX inference speed | 2026-08-10 |" in content
    assert "- Review bench results next Tuesday." in content


def test_eml_draft_creation_and_mime_headers(tmp_path: Path) -> None:
    """Verifies `.eml` draft creation and X-Unsent draft MIME header parsing."""
    draft = EmailDraft(
        subject="Follow-up: Q3 Architecture Sync",
        body="Here are the notes and action items from today...",
        recipients=["alex@company.internal", "sarah@company.internal"],
    )
    title = "Q3 Architecture Sync"
    timestamp = "20260805_1430"

    output_path = create_eml_draft(
        draft=draft,
        timestamp=timestamp,
        title=title,
        sender="assistant@local-ai.internal",
        output_dir=tmp_path,
    )

    assert output_path.exists()
    assert output_path.name == "20260805_1430_Q3_Architecture_Sync.eml"

    # Read binary bytes back using modern email policy to get an EmailMessage
    with open(output_path, "rb") as f:
        msg: EmailMessage = email.message_from_binary_file(
            f, policy=email.policy.default
        )  # type: ignore[assignment]

    assert msg["Subject"] == "Follow-up: Q3 Architecture Sync"
    assert msg["From"] == "assistant@local-ai.internal"
    assert msg["To"] == "alex@company.internal, sarah@company.internal"
    assert msg["X-Unsent"] == "1"
    assert "Here are the notes and action items" in msg.get_content()
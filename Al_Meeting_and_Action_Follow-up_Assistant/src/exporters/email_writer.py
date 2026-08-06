"""
Generates RFC-compliant .eml draft files using Python's stdlib email package.
Can be opened natively by Windows mail clients (Outlook, Thunderbird) as unsent drafts.
"""

from email.message import EmailMessage
import email.policy
from pathlib import Path
from typing import List, Optional

from config.settings import settings
from src.llm.schemas import EmailDraft


def create_eml_draft(
    draft: EmailDraft,
    timestamp: str,
    title: str,
    sender: str = "assistant@local-ai.internal",
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Serializes an EmailDraft Pydantic model into a `.eml` file.

    Args:
        draft: The structured EmailDraft containing subject, body, and recipients.
        timestamp: Formatted string 'YYYYMMDD_HHMM'.
        title: Meeting title used to construct a safe filename.
        sender: Placeholder sender address for the draft.
        output_dir: Optional output directory override (defaults to settings.outputs_dir).

    Returns:
        Path: Absolute path to the generated `.eml` file.
    """
    target_dir = output_dir or settings.outputs_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename to ensure Windows path safety
    safe_title = "".join(c if c.isalnum() else "_" for c in title).strip("_")
    filename = f"{timestamp}_{safe_title}.eml"
    output_path = target_dir / filename

    # Build MIME email message
    msg = EmailMessage(email.policy.default)
    msg["Subject"] = draft.subject
    msg["From"] = sender

    # Format recipients line
    recipients: List[str] = draft.recipients if draft.recipients else ["participants@local-ai.internal"]
    msg["To"] = ", ".join(recipients)

    # Add custom MIME header indicating this is an AI-generated draft
    msg["X-Unsent"] = "1"
    msg["X-Generator"] = "Local-Ollama-Meeting-Assistant"

    # Populate email body
    msg.set_content(draft.body)

    # Write binary MIME format to disk
    with open(output_path, "wb") as f:
        f.write(msg.as_bytes())

    print(f"[Exporter: EML] Saved unsent email draft to:\n  -> {output_path}")
    return output_path
"""
Formats a structured MeetingRecord into a clean Markdown document and writes
it to disk using the required naming convention: YYYYMMDD_HHMM_meeting_title.md
"""

from pathlib import Path
from typing import Optional

from config.settings import settings
from src.llm.schemas import MeetingRecord


def create_markdown_file(
    record: MeetingRecord,
    title: str,
    timestamp: str,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Serializes a MeetingRecord Pydantic model into a Markdown file on disk.

    Args:
        record: The consolidated MeetingRecord from the Reduce node.
        title: Human-readable meeting title.
        timestamp: Formatted string 'YYYYMMDD_HHMM'.
        output_dir: Optional directory override (defaults to settings.outputs_dir).

    Returns:
        Path: Absolute path to the generated `.md` file.
    """
    target_dir = output_dir or settings.outputs_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize meeting title for Windows file paths
    safe_title = "".join(c if c.isalnum() else "_" for c in title).strip("_")
    filename = f"{timestamp}_{safe_title}.md"
    output_path = target_dir / filename

    # Assemble Markdown document sections
    md_lines = [
        f"# {title}",
        f"**Date:** {timestamp[:8]} | **Generated via Local Ollama Meeting Assistant**\n",
        "## Summary",
        f"{record.summary}\n",
        "## Key Decisions",
    ]

    if record.key_decisions:
        for dec in record.key_decisions:
            md_lines.append(f"- {dec}")
    else:
        md_lines.append("_No explicit key decisions recorded._")

    md_lines.extend([
        "\n## Actions",
        "| Assignee | Action Item | Deadline |",
        "| :--- | :--- | :--- |",
    ])

    if record.actions:
        for act in record.actions:
            md_lines.append(f"| **{act.assignee}** | {act.task} | {act.deadline} |")
    else:
        md_lines.append("| _None_ | _No action items recorded_ | _N/A_ |")

    md_lines.extend(["\n## Next Steps"])
    if record.next_steps:
        for step in record.next_steps:
            md_lines.append(f"- {step}")
    else:
        md_lines.append("_No specific next steps recorded._")

    # Write UTF-8 encoded Markdown to disk
    content = "\n".join(md_lines)
    output_path.write_text(content, encoding="utf-8")
    
    print(f"[Exporter: MD] Saved Markdown summary to:\n  -> {output_path}")
    return output_path
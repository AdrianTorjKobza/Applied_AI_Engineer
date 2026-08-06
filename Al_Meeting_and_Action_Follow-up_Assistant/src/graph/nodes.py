"""
Defines the LangGraph node functions that process MeetingState across
transcript chunking, Map-Reduce summarization, Markdown export, and Email drafting.
"""

from typing import Dict, Any, List
from config.settings import settings
from src.graph.state import MeetingState
from src.llm.ollama_client import llm_client
from src.llm.schemas import MeetingRecord
from src.exporters.email_writer import create_eml_draft
from src.exporters.markdown_writer import create_markdown_file


def chunk_transcript_node(state: MeetingState) -> Dict[str, Any]:
    """
    Splits the formatted plaintext transcript into ~2,500-3,000 token segments
    along speaker turn boundaries to avoid cutting mid-sentence.
    """
    transcript = state.get("formatted_transcript", "")
    lines = transcript.split("\n")
    
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_word_count = 0
    
    # Rough approximation: 1 token ~= 0.75 words -> 2800 tokens ~= 2100 words
    word_limit = int(settings.chunk_token_limit * 0.75)

    for line in lines:
        line_words = len(line.split())

        if current_word_count + line_words > word_limit and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_word_count = line_words
        else:
            current_chunk.append(line)
            current_word_count += line_words

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    print(f"[Graph: Chunk] Split transcript into {len(chunks)} chunk(s).")
    return {"chunks": chunks}


def map_summarize_node(state: MeetingState) -> Dict[str, Any]:
    """
    Map Step: Iterates through chunks and extracts partial MeetingRecords.
    In LangGraph, this can also be fanned out using the Send() API for true parallelism.
    """
    chunks = state.get("chunks", [])
    partial_records: List[MeetingRecord] = []

    print(f"[Graph: Map] Running Ollama extraction across {len(chunks)} chunk(s)...")
    for idx, chunk in enumerate(chunks, 1):
        print(f"  -> Summarizing chunk {idx}/{len(chunks)}...")
        record = llm_client.summarize_chunk(chunk)
        partial_records.append(record)

    return {"partial_records": partial_records}


def reduce_synthesize_node(state: MeetingState) -> Dict[str, Any]:
    """
    Reduce Step: Aggregates partial records into a single deduplicated MeetingRecord.
    If only 1 chunk existed, we bypass the reduce LLM call to save time.
    """
    partials = state.get("partial_records", [])

    if not partials:
        raise ValueError("No partial records found to reduce.")

    if len(partials) == 1:
        print("[Graph: Reduce] Single chunk detected; bypassing reduce synthesis call.")
        return {"final_record": partials[0]}

    print(f"[Graph: Reduce] Synthesizing {len(partials)} partial records into final summary...")
    final_record = llm_client.reduce_records(partials)
    return {"final_record": final_record}


def write_markdown_node(state: MeetingState) -> Dict[str, Any]:
    """
    Automated Artifact Generation: Formats and saves the Markdown meeting record
    using the unique naming convention: YYYYMMDD_HHMM_meeting_title.md
    NO HITL required for this node.
    """
    record = state.get("final_record")
    title = state.get("meeting_title", "Untitled_Meeting")
    timestamp = state.get("meeting_timestamp", "20260805_1200")

    if not record:
        raise ValueError("Cannot write markdown: final_record is missing from state.")

    # Sanitize title for Windows filenames
    safe_title = "".join(c if c.isalnum() else "_" for c in title).strip("_")
    filename = f"{timestamp}_{safe_title}.md"
    output_path = settings.outputs_dir / filename

    # Build Markdown document
    md_lines = [
        f"# {title}",
        f"**Date:** {timestamp[:8]} | **Generated via Local Ollama Meeting Assistant**\n",
        "## Summary",
        f"{record.summary}\n",
        "## Key Decisions",
    ]
    for dec in record.key_decisions:
        md_lines.append(f"- {dec}")
    
    md_lines.extend(["\n## Actions", "| Assignee | Action Item | Deadline |", "| :--- | :--- | :--- |"])
    for act in record.actions:
        md_lines.append(f"| **{act.assignee}** | {act.task} | {act.deadline} |")

    md_lines.extend(["\n## Next Steps"])
    for step in record.next_steps:
        md_lines.append(f"- {step}")

    content = "\n".join(md_lines)
    output_path.write_text(content, encoding="utf-8")
    print(f"[Graph: Write MD] Automatically generated meeting record at:\n  -> {output_path}")

    return {"markdown_file_path": str(output_path)}


def draft_email_node(state: MeetingState) -> Dict[str, Any]:
    """
    Prepares the email draft payload. After this node completes, the LangGraph
    checkpointer will interrupt execution so the human can review/approve.
    """
    record = state.get("final_record")
    title = state.get("meeting_title", "Meeting Follow-up")

    if not record:
        raise ValueError("Cannot draft email: final_record is missing from state.")

    print("[Graph: Draft Email] Drafting follow-up email via Ollama...")
    email_draft = llm_client.generate_email_draft(title=title, record=record)
    
    # Reset approval state to None so HITL CLI knows it is pending
    return {
        "email_draft": email_draft,
        "email_approved": None,
    }

def write_eml_node(state: MeetingState) -> Dict[str, Any]:
    """
    Terminal Node: Writes the .eml file to disk ONLY IF email_approved is True.
    If email_approved is False, aborts without writing.
    """
    approved = state.get("email_approved")
    draft = state.get("email_draft")
    title = state.get("meeting_title", "Untitled_Meeting")
    timestamp = state.get("meeting_timestamp", "20260805_1200")

    if approved is False:
        print("[Graph: Write EML] HITL Reviewer REJECTED the email draft. No .eml file created.")
        return {"eml_file_path": None}

    if not draft:
        raise ValueError("Cannot write .eml: email_draft is missing from state.")

    # Execute file generation
    eml_path = create_eml_draft(draft=draft, timestamp=timestamp, title=title)
    return {"eml_file_path": str(eml_path)}

def write_markdown_node(state: MeetingState) -> Dict[str, Any]:
    """
    Automated Artifact Generation: Formats and saves the Markdown meeting record
    by delegating to the markdown_writer exporter.
    """
    record = state.get("final_record")
    title = state.get("meeting_title", "Untitled_Meeting")
    timestamp = state.get("meeting_timestamp", "20260805_1200")

    if not record:
        raise ValueError("Cannot write markdown: final_record is missing from state.")

    # Delegate file creation to the dedicated exporter
    output_path = create_markdown_file(
        record=record,
        title=title,
        timestamp=timestamp,
    )

    return {"markdown_file_path": str(output_path)}
"""
CLI entry point for the Local AI Meeting Assistant.
Orchestrates audio transcription, LangGraph state graph execution, interactive
Human-In-The-Loop (HITL) email approval, and artifact reporting.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from config.settings import settings
from src.graph.workflow import meeting_graph
from src.ingestion.diarization import DiarizationEngine

app = typer.Typer(
    name="local-meeting-assistant",
    help="Local-first AI Meeting Assistant powered by Ollama, WhisperX, and LangGraph.",
    add_completion=False,
)
console = Console()


@app.command()
def process(
    audio: Path = typer.Option(
        ...,
        "--audio",
        "-a",
        help="Path to the input audio file (.wav, .mp3, .m4a).",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    title: str = typer.Option(
        "Architecture Sync",
        "--title",
        "-t",
        help="Meeting title used in export filenames and email headers.",
    ),
    hf_token: Optional[str] = typer.Option(
        None,
        "--hf-token",
        "-k",
        help="Hugging Face access token for Pyannote speaker diarization (or set HF_TOKEN env var).",
    ),
) -> None:
    """
    Ingests an audio file, transcribes and diarizes speakers locally, synthesizes
    meeting records via LangGraph Map-Reduce, writes a Markdown report automatically,
    and prompts for HITL approval before drafting a local .eml email.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    thread_id = str(uuid.uuid4())
    thread_config = {"configurable": {"thread_id": thread_id}}

    console.print(
        Panel.fit(
            f"[bold green]Local AI Meeting Assistant[/bold green]\n"
            f"[bold white]Title:[/bold white] {title}\n"
            f"[bold white]Audio:[/bold white] {audio.name}\n"
            f"[bold white]Timestamp:[/bold white] {timestamp}",
            title="Pipeline Initializing",
            border_style="green",
        )
    )

    # -------------------------------------------------------------------------
    # 1. Ingestion & Diarization Phase (WhisperX + Pyannote)
    # -------------------------------------------------------------------------
    try:
        engine = DiarizationEngine(hf_token=hf_token)
        turns, formatted_transcript = engine.transcribe_and_diarize(
            audio_path=str(audio)
        )
    except Exception as e:
        console.print(f"[bold red]Ingestion Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Save intermediate transcript to data/transcripts/
    safe_title = "".join(c if c.isalnum() else "_" for c in title).strip("_")
    transcript_file = settings.transcripts_dir / f"{timestamp}_{safe_title}_transcript.txt"
    transcript_file.write_text(formatted_transcript, encoding="utf-8")
    console.print(f"[dim]Saved raw transcript to: {transcript_file}[/dim]\n")

    # -------------------------------------------------------------------------
    # 2. Initializing LangGraph State
    # -------------------------------------------------------------------------
    initial_state = {
        "audio_file_path": str(audio),
        "meeting_title": title,
        "meeting_timestamp": timestamp,
        "transcript_turns": turns,
        "formatted_transcript": formatted_transcript,
        "partial_records": [],
    }

    console.print("[bold blue]Starting LangGraph Map-Reduce Pipeline...[/bold blue]")

    # -------------------------------------------------------------------------
    # 3. First Execution Pass (Runs up to the HITL Interrupt)
    # -------------------------------------------------------------------------
    # The graph will execute:
    # chunk_transcript_node -> map_summarize_node -> reduce_synthesize_node ->
    # write_markdown_node (AUTOMATED) -> draft_email_node -> [PAUSE INTERRUPT]
    
    meeting_graph.invoke(initial_state, config=thread_config)

    # Retrieve state snapshot at the breakpoint
    state_snapshot = meeting_graph.get_state(thread_config)
    current_values = state_snapshot.values

    # Report automated Markdown output location
    md_path = current_values.get("markdown_file_path")
    if md_path:
        console.print(
            Panel(
                f"[bold green]Meeting Record Automatically Written![/bold green]\n"
                f"File: [yellow]{md_path}[/yellow]",
                title="Markdown Export Status",
                border_style="cyan",
            )
        )

    # -------------------------------------------------------------------------
    # 4. Human-in-the-Loop (HITL) Review for Email Draft
    # -------------------------------------------------------------------------
    email_draft = current_values.get("email_draft")
    
    if not email_draft:
        console.print("[red]Error: Email draft payload was not generated.[/red]")
        raise typer.Exit(code=1)

    # Display Email Draft details cleanly in terminal
    draft_preview = (
        f"[bold white]Subject:[/bold white] {email_draft.subject}\n"
        f"[bold white]Recipients:[/bold white] {', '.join(email_draft.recipients)}\n\n"
        f"[bold white]Body Preview:[/bold white]\n{email_draft.body}"
    )
    console.print(
        Panel(
            draft_preview,
            title="[bold yellow]Human-in-the-Loop Review: Outbound Email Draft[/bold yellow]",
            border_style="yellow",
        )
    )

    # Interactive Console Prompt
    approve = typer.confirm(
        "\nDo you approve this email draft to generate a local .eml file?",
        default=True,
    )

    # -------------------------------------------------------------------------
    # 5. Resume LangGraph Execution based on HITL Decision
    # -------------------------------------------------------------------------
    console.print("\n[bold blue]Resuming LangGraph execution...[/bold blue]")
    
    # Push human decision into graph state
    meeting_graph.update_state(
        thread_config,
        {"email_approved": approve},
    )

    # Resume graph from checkpoint to execute write_eml_node
    final_state_result = meeting_graph.invoke(None, config=thread_config)

    # -------------------------------------------------------------------------
    # 6. Final Summary Report
    # -------------------------------------------------------------------------
    eml_path = final_state_result.get("eml_file_path")

    if approve and eml_path:
        console.print(
            Panel.fit(
                f"[bold green]Success! Pipeline Completed.[/bold green]\n\n"
                f"• [bold white]Markdown Summary:[/bold white] {md_path}\n"
                f"• [bold white]Local Email Draft:[/bold white] {eml_path}\n\n"
                f"[dim]Double-click the .eml file to open directly in Outlook or Thunderbird.[/dim]",
                title="Execution Complete",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel.fit(
                f"[bold yellow]Pipeline Completed (Email Draft Rejected).[/bold yellow]\n\n"
                f"• [bold white]Markdown Summary Saved:[/bold white] {md_path}\n"
                f"• [bold white]Email Draft Status:[/bold white] Discarded (No .eml created)",
                title="Execution Complete",
                border_style="yellow",
            )
        )


if __name__ == "__main__":
    app()
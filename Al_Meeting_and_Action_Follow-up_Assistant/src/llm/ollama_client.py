"""
Wraps ChatOllama from langchain-ollama to execute structured JSON extraction
using Pydantic schemas. Imports system prompts cleanly from config.prompts.
"""

from typing import List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from config.prompts import (
    EMAIL_SYSTEM_PROMPT,
    MAP_SYSTEM_PROMPT,
    REDUCE_SYSTEM_PROMPT,
)
from config.settings import settings
from src.llm.schemas import EmailDraft, MeetingRecord


class LocalLLMClient:
    """
    Manages connections to the local Ollama instance and provides structured
    generation helpers for MeetingRecord and EmailDraft schemas.
    """

    def __init__(self) -> None:
        self.base_model = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
        )

        # Bind structured output schemas via Ollama JSON Schema capability
        self.meeting_record_extractor = self.base_model.with_structured_output(
            MeetingRecord,
            method="json_schema",
        )
        self.email_draft_extractor = self.base_model.with_structured_output(
            EmailDraft,
            method="json_schema",
        )

    def summarize_chunk(self, chunk_text: str) -> MeetingRecord:
        """
        Map Step: Extracts a partial MeetingRecord from a single transcript chunk.
        """
        messages = [
            SystemMessage(content=MAP_SYSTEM_PROMPT),
            HumanMessage(content=f"TRANSCRIPT CHUNK:\n\n{chunk_text}"),
        ]
        result = self.meeting_record_extractor.invoke(messages)
        return result

    def reduce_records(self, partial_records: List[MeetingRecord]) -> MeetingRecord:
        """
        Reduce Step: Consolidates multiple partial MeetingRecords into one final record.
        """
        # Serialize partials into a readable block for the LLM
        partials_text = "\n\n--- NEXT PARTIAL RECORD ---\n\n".join(
            [record.model_dump_json(indent=2) for record in partial_records]
        )
        messages = [
            SystemMessage(content=REDUCE_SYSTEM_PROMPT),
            HumanMessage(content=f"PARTIAL MEETING RECORDS:\n\n{partials_text}"),
        ]
        result = self.meeting_record_extractor.invoke(messages)
        return result

    def generate_email_draft(self, title: str, record: MeetingRecord) -> EmailDraft:
        """
        HITL Preparation Step: Drafts an outbound email based on the final MeetingRecord.
        """
        content_payload = (
            f"MEETING TITLE: {title}\n\n"
            f"FINAL MEETING RECORD:\n{record.model_dump_json(indent=2)}"
        )
        messages = [
            SystemMessage(content=EMAIL_SYSTEM_PROMPT),
            HumanMessage(content=content_payload),
        ]
        result = self.email_draft_extractor.invoke(messages)
        return result


# Shared singleton instance
llm_client = LocalLLMClient()
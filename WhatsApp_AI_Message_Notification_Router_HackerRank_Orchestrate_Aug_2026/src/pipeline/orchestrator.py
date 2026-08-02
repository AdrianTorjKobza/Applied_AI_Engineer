"""Asynchronous pipeline orchestrator tying together ingestion, reasoning, and rules."""

import asyncio
import logging
import pandas as pd
from tqdm import tqdm
from src.config import settings
from src.domain.exceptions import RouterDomainError
from src.domain.models import FinalOutputRow, IncomingMessage
from src.domain.rules import PolicyEngine
from src.services.audio_service import AudioService
from src.services.llm_router import OllamaRouterService
from src.services.vector_store import VectorStoreService
from src.utils.data_loader import DataLoader

logger = logging.getLogger(__name__)


class MessageRoutingOrchestrator:
    """Coordinates batch routing execution across all system components."""

    def __init__(self) -> None:
        self.loader = DataLoader()
        self.audio_service = AudioService()
        self.vector_store = VectorStoreService()
        self.llm_router = OllamaRouterService()
        self.semaphore = asyncio.Semaphore(settings.concurrent_requests)

    def setup(self) -> None:
        """Initializes data stores and indexes history."""
        logger.info("Initializing metadata loader and vector store...")
        self.loader.load_all()
        if not self.loader.history_df.empty:
            self.vector_store.index_history(self.loader.history_df)
        logger.info("Setup complete. System ready for message ingestion.")

    async def _process_single_message(self, msg: IncomingMessage) -> FinalOutputRow:
        """Processes a single message through transcription, retrieval, LLM, and rules."""
        async with self.semaphore:
            # 1. Audio Processing
            text_content = msg.message_text
            if msg.media_type == "voice" and msg.media_id:
                transcription = self.audio_service.transcribe(msg.media_id)
                text_content = f"{text_content} {transcription}".strip()

            # 2. Vector Evidence Retrieval
            evidence_ids = self.vector_store.find_evidence(
                query_text=text_content,
                sender_user_id=msg.sender_user_id,
            )

            # 3. Context Summary Building
            context_str = self.loader.get_context_summary(
                user_id=msg.user_id,
                group_id=msg.group_id,
                business_id=msg.business_id,
            )

            # 4. LLM Semantic Prediction
            llm_pred = await self.llm_router.predict_async(
                message_text=text_content,
                media_type=msg.media_type,
                media_id=msg.media_id or "",
                context_str=context_str,
                evidence_ids=evidence_ids,
            )

            # 5. Policy Rule Overrides
            user_meta = self.loader.get_user(msg.user_id)
            group_meta = (
                self.loader.get_group_member(msg.user_id, msg.group_id)
                if msg.group_id
                else None
            )

            final_pred = PolicyEngine.apply_overrides(
                prediction=llm_pred,
                created_at_str=msg.created_at,
                user_meta=user_meta,
                group_meta=group_meta,
            )

            return FinalOutputRow(
                message_id=msg.message_id,
                action=final_pred.action,
                message_type=final_pred.message_type,
                reason=final_pred.reason,
                confidence=round(final_pred.confidence, 2),
                evidence_message_ids=evidence_ids,
            )

    async def run(self) -> None:
        """Executes message routing against target messages.csv and writes output.csv.

        Raises:
            RouterDomainError: If messages.csv is empty or unreadable.
        """
        messages_path = settings.messages_csv_path
        if not messages_path.exists():
            raise RouterDomainError(f"Messages file missing at: {messages_path}")

        logger.info("Reading incoming messages from: %s", messages_path)
        messages_df = pd.read_csv(messages_path)

        if messages_df.empty:
            error_msg = f"Input file '{messages_path}' contains no message records."
            logger.error(error_msg)
            raise RouterDomainError(error_msg)

        messages = [
            IncomingMessage(
                message_id=str(row["message_id"]),
                user_id=str(row["user_id"]),
                conversation_type=str(row["conversation_type"]),
                group_id=str(row.get("group_id", "")),
                business_id=str(row.get("business_id", "")),
                sender_user_id=str(row.get("sender_user_id", "")),
                created_at=str(row["created_at"]),
                message_text=str(row.get("message_text", "")),
                media_type=str(row.get("media_type", "")),
                media_id=(
                    str(row.get("media_id", ""))
                    if pd.notna(row.get("media_id"))
                    else None
                ),
                forwarded_count=int(row.get("forwarded_count", 0)),
            )
            for _, row in messages_df.iterrows()
        ]

        logger.info("Executing asynchronous router for %d messages...", len(messages))
        tasks = [self._process_single_message(msg) for msg in messages]

        results: list[FinalOutputRow] = []
        for task in tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc="Routing Messages",
            unit="msg",
        ):
            result = await task
            results.append(result)

        # Ensure ordered mapping matching original input
        result_map = {r.message_id: r for r in results}
        ordered_rows = [result_map[msg.message_id].model_dump() for msg in messages]

        output_path = settings.output_csv_path
        output_df = pd.DataFrame(ordered_rows)
        output_df.to_csv(output_path, index=False)
        logger.info("Batch completed idempotently. Output saved to: %s", output_path)
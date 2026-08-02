"""Idempotent vector indexing and evidence retrieval service using ChromaDB."""

import logging
import pandas as pd
import chromadb
from src.config import settings
from src.domain.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Handles persistent vector storage and sender-prioritized evidence retrieval."""

    def __init__(self) -> None:
        try:
            settings.chroma_dir.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(settings.chroma_dir))
            self.collection = self.client.get_or_create_collection(name="message_history")
        except Exception as exc:
            logger.error("Failed to initialize ChromaDB store: %s", exc)
            raise VectorStoreError("Vector store initialization failed.") from exc

    def index_history(self, history_df: pd.DataFrame) -> None:
        """Idempotently indexes message history into ChromaDB using upserts.

        Args:
            history_df: Dataframe containing historical message data.
        """
        if history_df.empty:
            logger.info("Message history is empty. Skipping indexing.")
            return

        logger.info("Starting idempotent indexing of message history...")
        documents: list[str] = []
        metadatas: list[dict[str, str]] = []
        ids: list[str] = []

        for _, row in history_df.iterrows():
            msg_id = str(row["message_id"])
            sender = str(row.get("sender_user_id", "unknown"))
            text = str(row.get("message_text", ""))

            if not text.strip():
                continue

            ids.append(msg_id)
            documents.append(text)
            metadatas.append({"sender_user_id": sender})

            if len(ids) >= 500:
                self._upsert_batch(ids, documents, metadatas)
                ids, documents, metadatas = [], [], []

        if ids:
            self._upsert_batch(ids, documents, metadatas)
        logger.info("Vector index sync complete. Total records: %d", self.collection.count())

    def _upsert_batch(self, ids: list[str], documents: list[str], metadatas: list[dict[str, str]]) -> None:
        """Performs idempotent batch upsert into ChromaDB."""
        try:
            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        except Exception as exc:
            logger.error("Error during vector upsert batch: %s", exc)
            raise VectorStoreError("Failed to upsert batch into vector database.") from exc

    def find_evidence(self, query_text: str, sender_user_id: str | None = None, top_k: int = 2) -> str:
        """Retrieves matching evidence IDs prioritized by exact sender match first.

        Args:
            query_text: Message text to search.
            sender_user_id: Sender ID filter.
            top_k: Number of candidate evidence records to return.

        Returns:
            str: Semicolon-separated evidence IDs or 'none'.
        """
        if not query_text.strip() or self.collection.count() == 0:
            return "none"

        # Strategy 1: Priority match on exact sender_user_id
        if sender_user_id and sender_user_id != "nan":
            try:
                results = self.collection.query(
                    query_texts=[query_text],
                    n_results=top_k,
                    where={"sender_user_id": sender_user_id},
                )
                if results and results.get("ids") and len(results["ids"][0]) > 0:
                    return ";".join(results["ids"][0])
            except Exception as exc:
                logger.debug("Sender filter query yielded no match or exception: %s", exc)

        # Strategy 2: Fallback to general vector similarity match
        try:
            results = self.collection.query(query_texts=[query_text], n_results=top_k)
            if results and results.get("ids") and len(results["ids"][0]) > 0:
                return ";".join(results["ids"][0])
        except Exception as exc:
            logger.warning("Fallback semantic search failed: %s", exc)

        return "none"
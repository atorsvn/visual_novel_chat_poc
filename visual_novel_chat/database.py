"""SQLite conversation history helpers."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from .constants import DEFAULT_DB_PATH


logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Simple data structure describing a conversation message."""

    role: str
    content: str


class ConversationHistory:
    """Persist and retrieve Discord conversation history using SQLite."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self._init_db()
        logger.debug("ConversationHistory initialised with database at %s", self.db_path)

    # -- Database primitives -------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        logger.debug("Opening SQLite connection to %s", self.db_path)
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        logger.debug("Conversation table ensured for database %s", self.db_path)

    # -- Public API ----------------------------------------------------------

    def add_message(self, user_id: str, role: str, content: str) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversation (user_id, role, content)
                VALUES (?, ?, ?)
                """,
                (str(user_id), role, content),
            )
            conn.commit()
        logger.debug("Stored message for user %s with role %s", user_id, role)

    def get_conversation(self, user_id: str) -> List[ConversationMessage]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT role, content FROM conversation
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (str(user_id),),
            )
            rows = cursor.fetchall()
        messages = [ConversationMessage(role=row[0], content=row[1]) for row in rows]
        logger.debug("Retrieved %d conversation messages for user %s", len(messages), user_id)
        return messages

    def prune_conversation(self, user_id: str, max_messages: int = 9) -> None:
        """Limit the conversation to *max_messages* entries.

        The first message (expected to be the system prompt) is always retained
        while the remaining messages are trimmed from the beginning of the
        conversation.
        """

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id FROM conversation
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (str(user_id),),
            )
            rows = cursor.fetchall()
            if len(rows) > max_messages:
                ids_to_keep = {rows[0][0]} | {row[0] for row in rows[-(max_messages - 1) :]}
                ids_to_delete = [row_id for (row_id,) in rows if row_id not in ids_to_keep]
                if ids_to_delete:
                    cursor.executemany(
                        "DELETE FROM conversation WHERE id = ?",
                        [(row_id,) for row_id in ids_to_delete],
                    )
                    conn.commit()
                    logger.debug(
                        "Pruned %d old messages for user %s", len(ids_to_delete), user_id
                    )

    def add_messages(self, user_id: str, messages: Iterable[ConversationMessage]) -> None:
        message_list = list(messages)
        for message in message_list:
            self.add_message(user_id, message.role, message.content)
        logger.debug("Bulk stored %d messages for user %s", len(message_list), user_id)

    def clear(self) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation")
            conn.commit()
        logger.info("Cleared all conversation history from %s", self.db_path)

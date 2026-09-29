from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json

from asyncpg import Connection, Pool, Record
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)


MAX_HISTORY_MESSAGES = 100
MAX_SEARCH_RESULTS = 20


@dataclass(frozen=True, slots=True)
class HistoryRecord:
    message_id: int
    guild_id: int
    channel_id: int
    author_id: int
    author_is_bot: bool
    content: str
    created_at: datetime


class AIHistoryDB:
    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def load_recent_history(
        self,
        guild_id: int,
        channel_id: int,
        limit: int = 10,
        exclude_message_id: int | None = None,
        before_created_at: datetime | None = None,
    ) -> list[ModelMessage]:
        if limit <= 0:
            return []

        limit = min(limit, MAX_HISTORY_MESSAGES)

        async with self._pool.acquire() as conn:
            conn: Connection
            rows = await conn.fetch(
                """
                SELECT message_id, guild_id, channel_id, author_id,
                       author_is_bot, content, created_at
                FROM discord_messages
                WHERE guild_id = $1
                  AND channel_id = $2
                  AND deleted_at IS NULL
                  AND ($4::BIGINT IS NULL OR message_id <> $4)
                  AND (
                      $5::TIMESTAMPTZ IS NULL
                      OR created_at < $5
                      OR (
                          created_at = $5
                          AND ($4::BIGINT IS NULL OR message_id < $4)
                      )
                  )
                ORDER BY created_at DESC, message_id DESC
                LIMIT $3;
                """,
                guild_id,
                channel_id,
                limit,
                exclude_message_id,
                before_created_at,
            )

        return [self._to_model_message(row) for row in reversed(rows)]

    async def ingest_history(
        self,
        message_id: int,
        guild_id: int,
        channel_id: int,
        author_id: int,
        message: str,
        *,
        author_is_bot: bool = False,
        thread_id: int | None = None,
        reply_to_message_id: int | None = None,
        metadata: Mapping[str, object] | None = None,
        created_at: datetime | None = None,
        edited_at: datetime | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        created_at = created_at or datetime.now(timezone.utc)
        content_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()
        metadata_json = json.dumps(dict(metadata or {}))

        async with self._pool.acquire() as conn:
            conn: Connection
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO discord_messages (
                        message_id,
                        guild_id,
                        channel_id,
                        author_id,
                        author_is_bot,
                        thread_id,
                        content,
                        content_hash,
                        reply_to_message_id,
                        metadata,
                        created_at,
                        edited_at,
                        deleted_at
                    )
                    VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9,
                        $10::jsonb, $11, $12, $13
                    )
                    ON CONFLICT (message_id) DO UPDATE SET
                        guild_id = EXCLUDED.guild_id,
                        channel_id = EXCLUDED.channel_id,
                        author_id = EXCLUDED.author_id,
                        author_is_bot = EXCLUDED.author_is_bot,
                        thread_id = EXCLUDED.thread_id,
                        content = EXCLUDED.content,
                        content_hash = EXCLUDED.content_hash,
                        reply_to_message_id = EXCLUDED.reply_to_message_id,
                        metadata = EXCLUDED.metadata,
                        edited_at = COALESCE(
                            EXCLUDED.edited_at, discord_messages.edited_at
                        ),
                        deleted_at = COALESCE(
                            EXCLUDED.deleted_at, discord_messages.deleted_at
                        );
                    """,
                    message_id,
                    guild_id,
                    channel_id,
                    author_id,
                    author_is_bot,
                    thread_id,
                    message,
                    content_hash,
                    reply_to_message_id,
                    metadata_json,
                    created_at,
                    edited_at,
                    deleted_at,
                )

                if deleted_at is None:
                    await conn.execute(
                        """
                        DELETE FROM message_embeddings
                        WHERE message_id = $1
                          AND EXISTS (
                              SELECT 1
                              FROM embedding_jobs
                              WHERE message_id = $1
                                AND content_hash <> $2
                          );
                        """,
                        message_id,
                        content_hash,
                    )
                    await conn.execute(
                        """
                        INSERT INTO embedding_jobs (message_id, content_hash)
                        VALUES ($1, $2)
                        ON CONFLICT (message_id) DO UPDATE SET
                            content_hash = EXCLUDED.content_hash,
                            status = CASE
                                WHEN embedding_jobs.content_hash <>
                                    EXCLUDED.content_hash
                                THEN 'pending'
                                ELSE embedding_jobs.status
                            END,
                            attempts = CASE
                                WHEN embedding_jobs.content_hash <>
                                    EXCLUDED.content_hash
                                THEN 0
                                ELSE embedding_jobs.attempts
                            END,
                            available_at = CASE
                                WHEN embedding_jobs.content_hash <>
                                    EXCLUDED.content_hash
                                THEN NOW()
                                ELSE embedding_jobs.available_at
                            END,
                            updated_at = NOW(),
                            last_error = CASE
                                WHEN embedding_jobs.content_hash <>
                                    EXCLUDED.content_hash
                                THEN NULL
                                ELSE embedding_jobs.last_error
                            END;
                        """,
                        message_id,
                        content_hash,
                    )
                else:
                    await conn.execute(
                        """
                        DELETE FROM embedding_jobs WHERE message_id = $1;
                        """,
                        message_id,
                    )
                    await conn.execute(
                        """
                        DELETE FROM message_embeddings WHERE message_id = $1;
                        """,
                        message_id,
                    )

    async def search_history(
        self,
        guild_id: int,
        query: str,
        *,
        channel_id: int | None = None,
        channel_ids: Sequence[int] | None = None,
        limit: int = 5,
    ) -> list[HistoryRecord]:
        normalized_query = query.strip()
        if not normalized_query or limit <= 0:
            return []

        limit = min(limit, MAX_SEARCH_RESULTS)
        normalized_query = _escape_like(normalized_query)

        async with self._pool.acquire() as conn:
            conn: Connection
            if channel_ids is not None:
                searchable_channel_ids = list(dict.fromkeys(channel_ids))
                if not searchable_channel_ids:
                    return []

                rows = await conn.fetch(
                    """
                    SELECT message_id, guild_id, channel_id, author_id,
                           author_is_bot, content, created_at
                    FROM discord_messages
                    WHERE guild_id = $1
                      AND channel_id = ANY($2::BIGINT[])
                      AND deleted_at IS NULL
                      AND content ILIKE '%' || $3 || '%' ESCAPE '\\'
                    ORDER BY created_at DESC, message_id DESC
                    LIMIT $4;
                    """,
                    guild_id,
                    searchable_channel_ids,
                    normalized_query,
                    limit,
                )
            elif channel_id is None:
                rows = await conn.fetch(
                    """
                    SELECT message_id, guild_id, channel_id, author_id,
                           author_is_bot, content, created_at
                    FROM discord_messages
                    WHERE guild_id = $1
                      AND deleted_at IS NULL
                      AND content ILIKE '%' || $2 || '%' ESCAPE '\\'
                    ORDER BY created_at DESC, message_id DESC
                    LIMIT $3;
                    """,
                    guild_id,
                    normalized_query,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT message_id, guild_id, channel_id, author_id,
                           author_is_bot, content, created_at
                    FROM discord_messages
                    WHERE guild_id = $1
                      AND channel_id = $2
                      AND deleted_at IS NULL
                      AND content ILIKE '%' || $3 || '%' ESCAPE '\\'
                    ORDER BY created_at DESC, message_id DESC
                    LIMIT $4;
                    """,
                    guild_id,
                    channel_id,
                    normalized_query,
                    limit,
                )

        return [self._to_history_record(row) for row in rows]

    @staticmethod
    def _to_model_message(row: Record) -> ModelMessage:
        content = row["content"]
        created_at = row["created_at"]

        if row["author_is_bot"]:
            return ModelResponse(
                parts=[TextPart(content=content)],
                timestamp=created_at,
            )

        return ModelRequest(
            parts=[UserPromptPart(content=content, timestamp=created_at)],
            timestamp=created_at,
        )

    @staticmethod
    def _to_history_record(row: Record) -> HistoryRecord:
        return HistoryRecord(
            message_id=row["message_id"],
            guild_id=row["guild_id"],
            channel_id=row["channel_id"],
            author_id=row["author_id"],
            author_is_bot=row["author_is_bot"],
            content=row["content"],
            created_at=row["created_at"],
        )


def format_search_results(records: list[HistoryRecord]) -> str:
    if not records:
        return "No matching messages found."

    return "\n".join(
        f"[{record.created_at.isoformat()}] "
        f"<{record.author_id}> {record.content}"
        for record in records
    )


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

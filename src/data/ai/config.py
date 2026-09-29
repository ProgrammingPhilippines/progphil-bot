from asyncpg import Connection, Pool


class AIConfigDB:
    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def is_enabled_for_channel(
        self, guild_id: int, channel_id: int
    ) -> bool:
        async with self._pool.acquire() as conn:
            conn: Connection
            enabled = await conn.fetchval(
                """
                SELECT c.enabled
                FROM pph_ai_guild_config AS c
                JOIN pph_ai_channels AS ch ON ch.guild_id = c.guild_id
                WHERE c.guild_id = $1
                  AND ch.channel_id = $2;
                """,
                guild_id,
                channel_id,
            )

        return bool(enabled)

    async def toggle(self, guild_id: int) -> bool:
        async with self._pool.acquire() as conn:
            conn: Connection
            enabled = await conn.fetchval(
                """
                INSERT INTO pph_ai_guild_config (guild_id, enabled)
                VALUES ($1, TRUE)
                ON CONFLICT (guild_id) DO UPDATE SET
                    enabled = NOT pph_ai_guild_config.enabled,
                    updated_at = NOW()
                RETURNING enabled;
                """,
                guild_id,
            )

        return bool(enabled)

    async def set_channel(
        self, guild_id: int, channel_id: int, enabled: bool
    ) -> None:
        async with self._pool.acquire() as conn:
            conn: Connection
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO pph_ai_guild_config (guild_id)
                    VALUES ($1)
                    ON CONFLICT (guild_id) DO NOTHING;
                    """,
                    guild_id,
                )

                if enabled:
                    await conn.execute(
                        """
                        INSERT INTO pph_ai_channels (guild_id, channel_id)
                        VALUES ($1, $2)
                        ON CONFLICT (guild_id, channel_id) DO NOTHING;
                        """,
                        guild_id,
                        channel_id,
                    )
                else:
                    await conn.execute(
                        """
                        DELETE FROM pph_ai_channels
                        WHERE guild_id = $1 AND channel_id = $2;
                        """,
                        guild_id,
                        channel_id,
                    )

    async def get_channels(self, guild_id: int) -> list[int]:
        async with self._pool.acquire() as conn:
            conn: Connection
            rows = await conn.fetch(
                """
                SELECT channel_id
                FROM pph_ai_channels
                WHERE guild_id = $1
                ORDER BY channel_id;
                """,
                guild_id,
            )

        return [int(row["channel_id"]) for row in rows]

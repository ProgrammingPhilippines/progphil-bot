from asyncpg import Pool


class AnonymousPostingDB:
    """The database handler for the anonymous posting cog."""

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def _check(self, forum_id: int):
        """Checks if a forum already exists inside the database.

        :param forum_id: The forum id to check.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            result = await conn.fetch("""
                SELECT * FROM pph_anonymous_posting_forums
                WHERE forum_id = $1;
            """, forum_id)

            return bool(result)

    async def add_forums(self, forums: list[int]):
        """Adds forum ids in the database.

        :param forums: A list of forum objects.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            for forum in forums:
                if await self._check(forum):
                    continue

                await conn.execute("""
                    INSERT INTO pph_anonymous_posting_forums VALUES ($1)
                """, forum)

    async def remove_forums(self, forums: list[int]):
        """Removes forum ids in the database.

        :param forums: A list of forum objects.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            for forum in forums:
                if not await self._check(forum):
                    continue

                await conn.execute("""
                    DELETE FROM pph_anonymous_posting_forums
                    WHERE forum_id = $1
                """, forum)

    async def get_forums(self):
        """Gets a forum id in the database."""

        async with self._pool.acquire() as conn:
            conn: Pool

            forums = await conn.fetch("""
                SELECT * FROM pph_anonymous_posting_forums;
            """)

            return forums

    async def upsert_log_channel(self, channel_id: int):
        """Inserts a log channel to the database.

        :param channel_id: The channel id of the logging channel
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            count, = await conn.fetch("""
                SELECT COUNT(*) FROM pph_anonymous_posting_log_channel;
            """)

            if not count["count"]:
                stmt = """
                    INSERT INTO pph_anonymous_posting_log_channel
                    VALUES ($1)
                """
            else:
                stmt = """
                    UPDATE pph_anonymous_posting_log_channel
                    SET channel_id = $1
                """

            await conn.execute(stmt, channel_id)

    async def get_log_channel(self):
        """Get the log channel."""

        async with self._pool.acquire() as conn:
            conn: Pool

            channel_id = await conn.fetch("""
                SELECT channel_id FROM pph_anonymous_posting_log_channel;
            """)

            return channel_id

    async def upsert_current_view(self, message_id: int, channel_id: int):
        """Upserts the message view id."""

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                INSERT INTO pph_anon_view VALUES (1, $1, $2)
                ON CONFLICT (id)   
                    DO UPDATE SET message_id = $1, channel_id = $2;
            """, message_id, channel_id)

    async def get_view(self):
        """Get the message view id."""

        async with self._pool.acquire() as conn:
            conn: Pool

            message = await conn.fetch("""
                SELECT * FROM pph_anon_view;
            """)

            if message:
                return message[0]

        return None

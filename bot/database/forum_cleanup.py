from typing import Literal

from asyncpg import Pool


class ForumCleanupDB:
    """The database handler for Forum Cleanup."""

    def __init__(self, pool: Pool):
        self._pool = pool

    async def _check(self, forum_id: int):
        """Checks if a forum already exists inside the database.

        :param forum_id: The forum id to check.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            result = await conn.fetch("""
                SELECT * FROM pph_forum_cleanup_forums
                WHERE forum_id = $1;
            """, forum_id)

            return bool(result)

    async def add_forums(self, forums: list[int]):
        """Adds forum ids in the database.

        :param forums: A list of forum ids.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            for forum in forums:
                if await self._check(forum):
                    continue

                await conn.execute("""
                    INSERT INTO pph_forum_cleanup_forums VALUES ($1)
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
                    DELETE FROM pph_forum_cleanup_forums
                    WHERE forum_id = $1
                """, forum)

    async def get_forums(self):
        """Gets a forum id in the database."""

        async with self._pool.acquire() as conn:
            conn: Pool

            forums = await conn.fetch("""
                SELECT * FROM pph_forum_cleanup_forums;
            """)

            return forums

    async def upsert_schedule(self, duration_unit: Literal["day", "week"]):
        """Upserts a schedule in the db

        :parm duration_unit: The duration unit.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                INSERT INTO pph_forum_cleanup_sched VALUES (1, $1)
                ON CONFLICT (id)
                    DO UPDATE SET duration_unit = $1;
            """, duration_unit)

    async def get_schedule(self):
        """Gets a schedule in the db"""

        async with self._pool.acquire() as conn:
            conn: Pool

            sched = await conn.fetch("""
                SELECT duration_unit FROM pph_forum_cleanup_sched;
            """)

        return sched

    async def upsert_conf(self, conf_type: Literal["close"], num_days: int):
        """Upserts a configuration on forum cleanup

        :param conf_type: The configuration type
        :param num_days: The number of days
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                INSERT INTO pph_forum_cleanup_conf VALUES ($1, $2)
                ON CONFLICT (conf_type)
                    DO UPDATE SET num_days = $2;
            """, conf_type, num_days)

    async def get_conf(self):
        """Gets a configuration on forum cleanup"""

        async with self._pool.acquire() as conn:
            conn: Pool

            conf = await conn.fetch("""
                SELECT * FROM pph_forum_cleanup_conf;
            """)

        return conf

    async def upsert_message(self, trigger: str, message: str):
        """Upserts a closing/locking message. (the message send to the thread after closing.)

        :param message: The message to send.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                INSERT INTO pph_forum_cleanup_message(c_trigger, c_message)
                VALUES ($1, $2)
                ON CONFLICT (c_trigger) DO
                    UPDATE SET c_message = $2;
            """, trigger, message)

    async def get_message(self, trigger: str):
        """Gets the message to be sent after closing/locking the thread."""

        async with self._pool.acquire() as conn:
            conn: Pool

            message = await conn.fetch("""
                SELECT c_message FROM pph_forum_cleanup_message
                WHERE c_trigger = $1;
            """, trigger)

            return message

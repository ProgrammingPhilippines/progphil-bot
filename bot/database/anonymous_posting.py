from uuid import UUID

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

    async def insert_post(
        self,
        uuid: UUID,
        post_id: int,
        author: int,
        title: str
    ):
        """Inserts a post to the database.

        :param uuid: The post uuid
        :param post_id: The post id
        :param author: The author id
        :param title: The post title
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                INSERT INTO pph_anonymous_posting_posts VALUES ($1, $2, $3, $4);
            """, uuid, post_id, author, title)

    async def get_posts(self, author_id: int):
        """Gets all posts of an author.

        :param author_id: The author to check.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            posts = await conn.fetch("""
                SELECT * FROM pph_anonymous_posting_posts
                WHERE post_author = $1;
            """, author_id)

            return posts

    async def get_post(self, uuid: UUID):
        """Get a specific post with a uuid.

        :param uuid: The post uuid.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            post = await conn.fetch("""
                SELECT * FROM pph_anonymous_posting_posts
                WHERE post_uuid = $1;
            """, uuid)

            return post

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
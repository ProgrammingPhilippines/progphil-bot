from asyncpg import Pool


class DevHelpTagDB:
    def __init__(self, pool: Pool):
        self._pool = pool

    async def update(self, setting: str, value: int | str) -> None:
        """Sets the tag to apply to solved dev help thread

        :param id: The tag id.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            # I don't think this is vulnerable to sql injection
            # since this isn't exposed to any user input.

            await conn.execute(f"""
                INSERT INTO dev_help_solved (id, {setting}) VALUES (1, $1)
                ON CONFLICT (id)
                DO UPDATE SET {setting} = $1;
            """, value)

    async def get(self) -> int | None:
        """Gets the settings saved in the database."""

        async with self._pool.acquire() as conn:
            conn: Pool

            setting_r = await conn.fetch(f"""
                SELECT * FROM dev_help_solved;
            """)

        if not setting_r:
            return

        return setting_r[0]


class DevHelpViewsDB:
    def __init__(self, pool: Pool):
        self._pool = pool

    async def get_persistent_views(self):
        """Gets all persistent views."""

        async with self._pool.acquire() as conn:
            conn: Pool

            views = await conn.fetch(f"""
                SELECT * FROM pph_dev_help_views WHERE closed = false;
            """)

        return views

    async def close_view(self, view_id: int):
        """Closes a view from the database.

        :param view_id: The view id.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute(f"""
                UPDATE pph_dev_help_views SET closed = true WHERE thread_id = $1;
            """, view_id)

    async def add_view(self, thread_id: int, message_id: int,author_id: int):
        """Adds a view to the database.

        :param view_id: The view id.
        :param message_id: The message id.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute(f"""
                INSERT INTO pph_dev_help_views (thread_id, message_id, author_id) VALUES ($1, $2, $3);
            """, thread_id, message_id, author_id)

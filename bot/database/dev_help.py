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

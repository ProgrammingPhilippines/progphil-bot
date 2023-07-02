from asyncpg import Pool


class UserReminderDB:
    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def get_config(self) -> dict:
        """
        Gets the reminder message.

        :return: str
        """
        async with self._pool.acquire() as conn:
            conn: Pool

            message = await conn.fetchrow(f"""
                SELECT * FROM pph_user_reminder;
            """)

        return message if message is not None else None

    async def set_config(self, key: str, value: str | int) -> None:
        """
        Inserts the reminder message.

        :param message: Message
        """
        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute(f"""
                INSERT INTO pph_user_reminder(id, {key})
                VALUES (1, $1)
                ON CONFLICT (id)
                DO UPDATE SET {key} = $1;
            """, value)

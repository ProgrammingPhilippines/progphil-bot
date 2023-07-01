from asyncpg import Pool


class UserReminderDB:
    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def get_message(self) -> str:
        """
        Gets the reminder message.

        :return: str
        """
        async with self._pool.acquire() as conn:
            conn: Pool

            message = await conn.fetchrow("""
                SELECT message FROM pph_user_reminder;
            """)

        return message if message is not None else None

    async def update(self, message: str) -> None:
        """
        Updates the reminder message.

        :param message: Message
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                UPDATE pph_user_reminder 
                    SET message = $1
            """, message)

    async def insert(self, message: str) -> None:
        """
        Inserts the reminder message.

        :param message: Message
        """
        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                INSERT INTO pph_user_reminder(message)
                    VALUES ($1);
            """, message)


from asyncpg import Pool


class WelcomeDB:
    def __init__(self, pool: Pool):
        self._pool = pool

    async def set_message(self, message: str):
        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                INSERT INTO pph_welcomer VALUES (1, $1)
                ON CONFLICT (message_id)
                DO UPDATE SET message = $1;
            """, message)

    async def get_message(self) -> str:
        async with self._pool.acquire() as conn:
            conn: Pool

            message = await conn.fetch("""
                SELECT * FROM pph_welcomer;
            """)

            return message

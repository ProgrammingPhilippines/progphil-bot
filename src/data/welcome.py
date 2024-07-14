from asyncpg import Pool, Connection


class WelcomeDB:
    def __init__(self, pool: Pool):
        self._pool = pool

    async def set_message(self, message: str):
        async with self._pool.acquire() as conn:
            conn: Connection
            await conn.execute("""
                INSERT INTO pph_welcomer (message_id, message) VALUES (1, $1)
                ON CONFLICT (message_id)
                DO UPDATE SET message = $1;
            """, message)

    async def get_message(self):
        async with self._pool.acquire() as conn:
            conn: Connection
            message = await conn.fetchrow("""
                SELECT message FROM pph_welcomer WHERE message_id = 1
            """)
            return message
        

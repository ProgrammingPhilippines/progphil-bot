from asyncpg import Pool


class TriviaDB:
    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def get_config(self) -> dict:
        """Gets the trivia config."""
        async with self._pool.acquire() as conn:
            conn: Pool

            config = await conn.fetchrow("""
                SELECT * FROM pph_trivia;
            """)

        return dict(config)

    async def update_config(self, channel_id: str, schedule: str) -> None:
        """Updates the trivia config."""

        config = await self.get_config()

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                UPDATE pph_trivia 
                    SET channel_id = $1, schedule = $2
                    WHERE channel_id = $3 AND schedule = $4;
            """, channel_id, schedule, config["channel_id"], config["schedule"])

    async def insert_config(self, channel_id: str, schedule: str) -> None:
        """Inserts the trivia config."""
        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                INSERT INTO pph_trivia(channel_id, schedule)
                    VALUES ($1, $2);
            """, channel_id, schedule)



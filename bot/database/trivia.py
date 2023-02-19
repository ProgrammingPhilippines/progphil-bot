from asyncpg import Pool


class TriviaDB:
    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def get_config(self) -> dict:
        """
        Gets the trivia config.

        :return: Dict
        """
        async with self._pool.acquire() as conn:
            conn: Pool

            config = await conn.fetchrow("""
                SELECT * FROM pph_trivia;
            """)

        return dict(config) if config else None

    async def update(self, channel_id: int, schedule: str) -> None:
        """
        Updates the trivia config.

        :param channel_id: Channel id
        :param schedule: Schedule
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                UPDATE pph_trivia 
                    SET channel_id = $1, schedule = $2
            """, channel_id, schedule)

    async def insert(self, channel_id: int, schedule: str) -> None:
        """
        Inserts the trivia config.

        :param channel_id: Channel id
        :param schedule: Schedule
        """
        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                INSERT INTO pph_trivia(channel_id, schedule)
                    VALUES ($1, $2);
            """, channel_id, schedule)

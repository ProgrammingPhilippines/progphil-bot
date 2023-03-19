from asyncpg import Pool


class JobHiringDB:
    def __int__(self, pool: Pool):
        self._pool = pool

    async def get_config(self) -> dict:
        async with self._pool.acquire() as conn:
            conn: Pool

            config = await conn.fetchrow("""
                SELECT * FROM pph_job_hiring;
            """)

        return dict(config) if config is not None else None

    def update(self, channel_id: int, schedule: str) -> None:
        ...

    def insert(self, channel_id: int, schedule: str) -> None:
        ...

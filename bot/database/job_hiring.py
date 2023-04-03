from asyncpg import Pool


class JobHiringDB:
    def __init__(self, pool: Pool):
        self._pool = pool

    async def get_config(self) -> dict:
        async with self._pool.acquire() as conn:
            conn: Pool

            config = await conn.fetchrow("""
                SELECT * FROM pph_job_hiring;
            """)

        return dict(config) if config is not None else None

    async def update(self, channel_id: int, schedule: str, schedule_type: int) -> None:
        conn: Pool

        async with self._pool.acquire() as conn:
            await conn.execute("""
                UPDATE pph_job_hiring 
                    SET channel_id = $1, schedule = $2, schedule_type = $3
            """, channel_id, schedule, schedule_type)

    async def insert(self, channel_id: int, schedule: str, schedule_type: int) -> None:
        conn: Pool

        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO pph_job_hiring(channel_id, schedule, schedule_type)
                    VALUES ($1, $2, $3);
            """, channel_id, schedule, schedule_type)

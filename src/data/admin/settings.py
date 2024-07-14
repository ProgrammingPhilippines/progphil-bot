from asyncpg import Pool


class Settings:
    def __init__(self, pool: Pool):
        self._pool = pool

    async def set_setting(self, key: str, value: str | int):
        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                INSERT INTO pph_settings VALUES ($1, $2)
                ON CONFLICT (setting_key)
                DO UPDATE SET setting_value = $2;
            """, key, value)

    async def get_setting(self, key: str):
        async with self._pool.acquire() as conn:
            conn: Pool

            setting = await conn.fetch("""
                SELECT * FROM pph_settings
                WHERE setting_key = $1;
            """, key)

            if not setting:
                return 0

            setting, = setting

            return setting["setting_value"]

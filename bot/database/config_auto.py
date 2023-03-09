from typing import Any

from asyncpg import Pool


class Config:
    """The database for configuration."""

    def __init__(self, pool: Pool):
        self._pool = pool

    async def get_config(self, key: str) -> Any:
        """Gets a configuration based on the key.

        :param key: The configuration to look for.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            config, = await conn.fetch("""
                SELECT * FROM pph_config_auto
                WHERE config_type = $1
            """, key)

        return config

    async def toggle_config(self, key: str) -> bool:
        """Toggles a configuration based on the key.

        :param key: The configuration to look for.
        """
        async with self._pool.acquire() as conn:
            conn: Pool

            config, = await conn.fetch("""
                SELECT * FROM pph_config_auto
                WHERE config_type = $1
            """, key)
            # Get the config status
            config = dict(config)["config_status"]
            # Toggle the status
            # `not` keyword just kind of reverses the bool instance
            await conn.execute("""
                UPDATE pph_config_auto SET config_status = $1 WHERE config_type = $2;
            """, not config, key)

        return not config

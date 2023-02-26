from typing import Literal

from asyncpg import Pool


class HelpersDB:
    """The database handler for PPH Helpers."""

    def __init__(self, pool: Pool):
        self._pool = pool

    async def _check_helper(self, helper_id: int) -> bool:
        async with self._pool.acquire() as conn:
            conn: Pool

            result = await conn.fetch("""
                SELECT * FROM pph_helpers
                WHERE id = $1;
            """, helper_id)

            if result:
                return True
            return False

    async def _check_obj(self, obj_id: int) -> bool:
        async with self._pool.acquire() as conn:
            conn: Pool

            result = await conn.fetch("""
                SELECT * FROM pph_helpers
                WHERE obj_id = $1;
            """, obj_id)

            if result:
                return True
            return False

    async def add_helper(self, obj_id: int, obj_type: Literal["role", "user"]) -> None:
        """Adds a 'helper' to the database.

        :param obj_id: The object id, user id or role id
        :param obj_type: The object type, user or role
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            if await self._check_obj(obj_id):
                return

            await conn.execute("""
                INSERT INTO pph_helpers(
                    obj_id,
                    obj_type
                ) VALUES ($1, $2);
            """, obj_id, obj_type)

    async def remove_helper(self, helper_id: int) -> bool:
        """Removes helpers from the database.

        :param helper_id: The object id to delete
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            if not await self._check_helper(helper_id):
                return False

            await conn.execute("""
                DELETE FROM pph_helpers
                WHERE id = $1
            """, helper_id)

            return True

    async def view_helpers(self) -> list[tuple[int, int, str]]:
        """Views all recorded helpers."""

        async with self._pool.acquire() as conn:
            conn: Pool

            helpers = await conn.fetch("""
                SELECT * FROM pph_helpers;
            """)

            return helpers

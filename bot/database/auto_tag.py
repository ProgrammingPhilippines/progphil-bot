from typing import Literal

from asyncpg import Pool


class AutoTagDB:
    """The database handler for PPH AutoTagging."""

    def __init__(self, pool: Pool):
        self._pool = pool

    async def _check_entry(self, helper_id: int) -> bool:
        async with self._pool.acquire() as conn:
            conn: Pool

            result = await conn.fetch("""
                SELECT * FROM pph_auto_tag
                WHERE id = $1;
            """, helper_id)

            if result:
                return True
            return False

    async def _check_obj(self, obj_id: int) -> bool:
        async with self._pool.acquire() as conn:
            conn: Pool

            result = await conn.fetch("""
                SELECT * FROM pph_auto_tag
                WHERE obj_id = $1;
            """, obj_id)

            if result:
                return True
            return False

    async def add_entry(
        self,
        obj_id: int,
        obj_type: Literal["role", "user"],
        tag_in: int,
        msg: str
    ) -> None:
        """Adds an `entry' to the database.

        :param obj_id: The object id, user id or role id
        :param obj_type: The object type, user or role
        :param tag_in: The forum to tag in
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            if await self._check_obj(obj_id):
                return

            await conn.execute("""
                INSERT INTO pph_auto_tag(
                    obj_id,
                    obj_type,
                    tag_in,
                    msg
                ) VALUES ($1, $2, $3, $4);
            """, obj_id, obj_type, tag_in, msg)

    async def remove_entry(self, entry_id: int) -> bool:
        """Removes entries from the database.

        :param entry_id: The object id to delete
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            if not await self._check_entry(entry_id):
                return False

            await conn.execute("""
                DELETE FROM pph_auto_tag
                WHERE id = $1
            """, entry_id)

            return True

    async def view_entries(self) -> list[tuple[int, int, str, int, str]]:
        """Views all recorded entries."""

        async with self._pool.acquire() as conn:
            conn: Pool

            entries = await conn.fetch("""
                SELECT * FROM pph_auto_tag;
            """)

            return entries

    async def view_from_forum(self, forum_id: int) -> list[tuple[int, int, str, int, str]]:
        """Views entries from forum id.

        :param forum_id: The forum id to view from.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            entries = await conn.fetch("""
                SELECT * FROM pph_auto_tag
                WHERE tag_in = $1;
            """, forum_id)

            return entries

from typing import Literal

from asyncpg import Pool, Record


class AutoTagDB:
    """The database handler for PPH AutoTagging."""

    def __init__(self, pool: Pool):
        self._pool = pool

    async def check_entry(self, entry_id: int) -> bool:
        async with self._pool.acquire() as conn:
            conn: Pool

            result = await conn.fetch("""
                SELECT * FROM pph_auto_tag
                WHERE id = $1;
            """, entry_id)

            if result:
                return True
            return False

    async def upsert_entry(
        self,
        obj_id: int,
        obj_type: Literal["role", "user"],
        forum_id: int,
        custom_msg: str
    ) -> None:
        """Adds/Updates an `entry' to the database.

        :param obj_id: The object id, user id or role id
        :param obj_type: The object type, user or role
        :param forum_id: The forum to tag in
        :param custom_msg: The custom message for this entry
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                INSERT INTO pph_auto_tag(
                    obj_id,
                    obj_type,
                    forum_id,
                    c_message
                ) VALUES ($1, $2, $3, $4)
                ON CONFLICT (forum_id)
                DO
                    UPDATE SET obj_id = $1, obj_type = $2, c_message = $4;
            """, obj_id, obj_type, forum_id, custom_msg)

    async def remove_entry(self, entry_id: int) -> bool:
        """Removes entries from the database.

        :param entry_id: The object id to delete
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            if not await self.check_entry(entry_id):
                return False

            await conn.execute("""
                DELETE FROM pph_auto_tag
                WHERE id = $1
            """, entry_id)

            return True

    async def view_entries(self) -> list[Record]:
        """Views all recorded entries."""

        async with self._pool.acquire() as conn:
            conn: Pool

            entries = await conn.fetch("""
                SELECT * FROM pph_auto_tag;
            """)

            return entries

    async def get_entry(self, forum_id: int) -> list[Record]:
        """Views entries from forum id.

        :param forum_id: The forum id to view from
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            entry = await conn.fetch("""
                SELECT * FROM pph_auto_tag
                WHERE forum_id = $1;
            """, forum_id)

            return entry[0] if entry else None

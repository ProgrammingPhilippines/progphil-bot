from typing import Literal

from asyncpg import Pool


class AutoTagDB:
    """The database handler for PPH AutoTagging."""

    def __init__(self, pool: Pool):
        self._pool = pool

    async def _check_entry(self, entry_id: int) -> bool:
        async with self._pool.acquire() as conn:
            conn: Pool

            result = await conn.fetch("""
                SELECT * FROM pph_auto_tag
                WHERE id = $1;
            """, entry_id)

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
        tag_in: int
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
                    tag_in
                ) VALUES ($1, $2, $3);
            """, obj_id, obj_type, tag_in)

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

    async def upsert_forum_message(self, forum_id: int, message: str):
        """Sets a custom forum message

        :param message: The custom message to send to a forum.
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            check = await conn.fetch("""
                SELECT * FROM pph_auto_tag_messages
                WHERE forum_id = $1;
            """, forum_id)

            if check:
                await conn.execute("""
                    UPDATE pph_auto_tag_messages SET msg = $1
                    WHERE forum_id = $2;
                """, message, forum_id)
            else:
                await conn.execute("""
                    INSERT INTO pph_auto_tag_messages(forum_id, msg)
                    VALUES ($1, $2);
                """, forum_id, message)

    async def get_custom_message(self, forum_id: int):
        """Gets the custom message set for the forum."""

        async with self._pool.acquire() as conn:
            conn: Pool

            message = await conn.fetch("""
                SELECT msg FROM pph_auto_tag_messages
                WHERE forum_id = $1;
            """, forum_id)

            if message:
                return dict(message[0])["msg"]

            return None

    async def get_all_messages(self):
        """Gets all custom messages."""

        async with self._pool.acquire() as conn:
            conn: Pool

            messages = await conn.fetch("""
                SELECT * FROM pph_auto_tag_messages
            """)

            return map(dict, messages)

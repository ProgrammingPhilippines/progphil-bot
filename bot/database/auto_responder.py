from aiomysql import (
    Pool,
    Cursor,
)


class AutoRespondDB:
    """The database handler for the auto responder cog."""

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def close(self) -> None:
        self._pool.close()
        await self._pool.wait_closed()

    async def insert_response(self, message: str,
                              response: str, response_type: str) -> None:
        """Inserts a response to the database.

        :param message: The message to respond to.
        :param response: The response to that message.
        :param response_type: The response type
        """

        async with self._pool.acquire() as conn:
            cursor: Cursor = await conn.cursor()

            await cursor.execute("""
                INSERT INTO pph_auto_responses(
                    message,
                    response,
                    response_type
                ) VALUES (%s, %s, %s);
            """, (message, response, response_type))
            await conn.commit()

    async def delete_response(self, response_id: int) -> None:
        """Deletes a response from the database.

        :param response_id: The id of the response to delete.
        """

        async with self._pool.acquire() as conn:
            cursor: Cursor = await conn.cursor()

            await cursor.execute("""
                DELETE FROM pph_auto_responses WHERE id = %s;
            """, (response_id,))

            await conn.commit()

    async def get_responses(self, offset: int = None) -> list[dict[str, str]]:
        """Gets all message and their responses from the database.

        :returns: dictionary with message as keys and responses as values.
        """

        # We'll fill this with dicts that has messages and their responses.
        results = []
        limit = 5

        async with self._pool.acquire() as conn:
            cursor: Cursor = await conn.cursor()

            if offset is not None:
                await cursor.execute("""
                    SELECT * FROM pph_auto_responses LIMIT %s OFFSET %s;
                """, (limit, offset))
            else:
                await cursor.execute("""
                    SELECT * FROM pph_auto_responses;
                """)

            # Loop over all the results and parse into dict.
            # The append the dict to the list
            for responses in await cursor.fetchall():
                id, message, response, rtype = responses
                results.append({
                    "id": id,
                    "message": message,
                    "response": response,
                    "rtype": rtype
                })

        return results

    async def records_count(self) -> int:
        """Gets the number of responses stored in the database"""

        async with self._pool.acquire() as conn:
            cursor: Cursor = await conn.cursor()

            await cursor.execute("""
                SELECT COUNT(*) FROM pph_auto_responses;
            """)

            count, = await cursor.fetchone()

            return count

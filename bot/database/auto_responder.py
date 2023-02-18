from asyncpg import Pool


class AutoRespondDB:
    """The database handler for the auto responder cog."""

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def _check_item(self, response_id: int) -> bool:
        """Checks if a response is already in the database.

        :param response_id: The response id
        """

        async with self._pool.acquire() as conn:
            conn: Pool  # This just serves as a typehint

            item = await conn.fetch("""
                SELECT * FROM pph_auto_responses WHERE id = $1
            """, response_id)

        return bool(item)

    async def insert_response(self, message: str,
                              response: str, response_type: str) -> None:
        """Inserts a response to the database.

        :param message: The message to respond to.
        :param response: The response to that message.
        :param response_type: The response type
        """

        async with self._pool.acquire() as conn:
            conn: Pool  # This just serves as a typehint

            await conn.execute("""
                INSERT INTO pph_auto_responses(
                    message,
                    response,
                    response_type
                ) VALUES ($1, $2, $3);
            """, message, response, response_type)

    async def delete_response(self, response_id: int) -> bool:
        """Deletes a response from the database.

        :param response_id: The id of the response to delete.
        :returns: Wether the delete was successful or not
        """

        if not await self._check_item(response_id):
            # Return false if the item does not exist
            return False

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                DELETE FROM pph_auto_responses WHERE id = $1;
            """, response_id)

        return True

    async def get_responses(self, offset: int = None) -> list[dict[str, str]]:
        """Gets all message and their responses from the database.

        :returns: dictionary with message as keys and responses as values.
        """

        # We'll fill this with dicts that has messages and their responses.
        results = []
        limit = 5

        async with self._pool.acquire() as conn:
            conn: Pool

            if offset is not None:
                data = await conn.fetch("""
                    SELECT * FROM pph_auto_responses LIMIT $1 OFFSET $2;
                """, limit, offset)
            else:
                data = await conn.fetch("""
                    SELECT * FROM pph_auto_responses;
                """)

            # Loop over all the results and parse into dict.
            # The append the dict to the list
            for responses in data:
                results.append(dict(responses))

        return results

    async def records_count(self) -> int:
        """Gets the number of responses stored in the database"""

        async with self._pool.acquire() as conn:
            conn: Pool

            count, = await conn.fetch("""
                SELECT COUNT(*) FROM pph_auto_responses;
            """)

            return count["count"]

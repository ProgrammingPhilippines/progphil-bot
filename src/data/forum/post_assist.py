from asyncpg import Pool


class PostAssistDB:
    def __init__(self, pool: Pool):
        self._pool = pool

    async def get_config(self, id: int):
        """Get a configuration from the database.

        :param id: The id of the configuration
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            config = await conn.fetchrow("""
                SELECT * FROM pph_post_assist_config
                WHERE id = $1;
            """, id)

        return config if config is not None else None

    async def config_by_forum(self, forum_id: int):
        """Get a configuration from the database by forum id.

        :param forum_id: The id of the configuration
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            config = await conn.fetchrow("""
                SELECT * FROM pph_post_assist_config
                WHERE forum_id = $1;
            """, forum_id)

        return config if config is not None else None

    async def get_reply(self, config_id: int):
        """Get a configuration from the database.

        :param config_id: The id of the configuration
        """

        if not await self.get_config(config_id):
            return

        async with self._pool.acquire() as conn:
            conn: Pool

            config = await conn.fetchrow("""
                SELECT * FROM pph_post_assist_reply
                WHERE configuration_id = $1;
            """, config_id)

        return config["custom_message"] if config is not None else None

    async def get_tags(self, config_id: int):
        """Get a configuration from the database.

        :param config_id: The id of the configuration
        """

        if not await self.get_config(config_id):
            return

        async with self._pool.acquire() as conn:
            conn: Pool

            config = await conn.fetch("""
                SELECT * FROM pph_post_assist_tags
                WHERE configuration_id = $1;
            """, config_id)

        return config or []

    async def get_tag_message(self, config_id: int):
        """Get a configuration from the database.

        :param config_id: The id of the configuration
        """

        if not await self.get_config(config_id):
            return

        async with self._pool.acquire() as conn:
            conn: Pool

            config = await conn.fetchrow("""
                SELECT * FROM pph_post_assist_tag_message
                WHERE configuration_id = $1;
            """, config_id)

        return config["custom_message"] if config is not None else None

    async def list_configurations(self):
        """Lists all configurations from the database."""

        async with self._pool.acquire() as conn:
            conn: Pool

            configs = await conn.fetch("""
                SELECT * FROM pph_post_assist_config;
            """)

            configurations = []

            for config in configs:
                new = {}
                new["id"] = config["id"]
                new["forum_id"] = config["forum_id"]
                new["tags"] = await self.get_tags(config["id"])
                new["tag_message"] = await self.get_tag_message(config["id"])
                new["reply"] = await self.get_reply(config["id"])
                configurations.append(new)

        return configurations

    async def add_configuration(
        self,
        forum_id: int,
        entities: list[tuple[int, str]],
        entity_tag_message: str,
        reply: str
    ):
        """Adds a configuration to the database.

        :param forum_id: The forum id to add to
        :param entities: The entities to add
        :param entity_tag_message: The tag message
        :param reply: The reply message
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                INSERT INTO pph_post_assist_config(
                    forum_id
                ) VALUES ($1)
            """, forum_id)

            config = await conn.fetchrow("""
                SELECT * FROM pph_post_assist_config
                WHERE forum_id = $1;
            """, forum_id)

            for entity_id, entity_type in entities:
                await conn.execute("""
                    INSERT INTO pph_post_assist_tags(
                        configuration_id,
                        entity_id,
                        entity_type
                    ) VALUES ($1, $2, $3)
                """, config["id"], entity_id, entity_type)

            await conn.execute("""
                INSERT INTO pph_post_assist_tag_message(
                    configuration_id,
                    custom_message
                ) VALUES ($1, $2)
            """, config["id"], entity_tag_message)

            await conn.execute("""
                INSERT INTO pph_post_assist_reply(
                    configuration_id,
                    custom_message
                ) VALUES ($1, $2)
            """, config["id"], reply)

    async def update_configuration(
        self,
        id: int,
        forum_id: int,
        entities: list[tuple[int, str]],
        entity_tag_message: str,
        reply: str
    ):
        """Updates a configuration to the database.

        :param id: The configuration id to update
        :param entities: The entities to add
        :param entity_tag_message: The tag message
        :param reply: The reply message
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            config = await self.get_config(id)

            if not config:
                return

            await conn.execute("""
                UPDATE pph_post_assist_config SET
                    forum_id = $1
                WHERE id = $2;
            """, forum_id, id)

            await conn.execute("""
                DELETE FROM pph_post_assist_tags WHERE configuration_id = $1;
            """, id)

            for entity_id, entity_type in entities:
                await conn.execute("""
                    INSERT INTO pph_post_assist_tags(
                        configuration_id,
                        entity_id,
                        entity_type
                    ) VALUES ($1, $2, $3)
                
                """, config["id"], entity_id, entity_type)

            await conn.execute("""
                UPDATE pph_post_assist_tag_message SET
                    custom_message = $1
                WHERE configuration_id = $2;
            """, entity_tag_message, config["id"])

            await conn.execute("""
                UPDATE pph_post_assist_reply SET
                    custom_message = $1
                WHERE configuration_id = $2;
            """, reply, config["id"])

    async def delete_configuration(self, id: int):
        """Deletes a configuration from the database.

        :param id: The configuration id to delete
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute("""
                DELETE FROM pph_post_assist_config WHERE id = $1;
            """, id)


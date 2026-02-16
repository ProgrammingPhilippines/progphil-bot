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

            config = await conn.fetchrow(
                """
                SELECT * FROM pph_post_assist_config
                WHERE id = $1;
            """,
                id,
            )

        return config if config is not None else None

    async def config_by_forum(self, forum_id: int):
        """Get a configuration from the database by forum id.

        :param forum_id: The id of the configuration
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            config = await conn.fetchrow(
                """
                SELECT * FROM pph_post_assist_config
                WHERE forum_id = $1;
            """,
                forum_id,
            )

        return config if config is not None else None

    async def get_reply(self, config_id: int):
        """Get a configuration from the database.

        :param config_id: The id of the configuration
        """

        if not await self.get_config(config_id):
            return

        async with self._pool.acquire() as conn:
            conn: Pool

            config = await conn.fetchrow(
                """
                SELECT * FROM pph_post_assist_reply
                WHERE configuration_id = $1;
            """,
                config_id,
            )

        return config["custom_message"] if config is not None else None

    async def get_tags(self, config_id: int):
        """Get a configuration from the database.

        :param config_id: The id of the configuration
        """

        if not await self.get_config(config_id):
            return

        async with self._pool.acquire() as conn:
            conn: Pool

            config = await conn.fetch(
                """
                SELECT * FROM pph_post_assist_tags
                WHERE configuration_id = $1;
            """,
                config_id,
            )

        return config or []

    async def get_tag_message(self, config_id: int):
        """Get a configuration from the database.

        :param config_id: The id of the configuration
        """

        if not await self.get_config(config_id):
            return

        async with self._pool.acquire() as conn:
            conn: Pool

            config = await conn.fetchrow(
                """
                SELECT * FROM pph_post_assist_tag_message
                WHERE configuration_id = $1;
            """,
                config_id,
            )

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
        reply: str,
        enable_accept_solutions: bool,
        enable_mark_as_solved: bool = False,
    ):
        """Adds a configuration to the database.

        :param forum_id: The forum id to add to
        :param entities: The entities to add
        :param entity_tag_message: The tag message
        :param reply: The reply message
        :param enable_accept_solutions: Whether to enable accept solutions
        :param enable_mark_as_solved: Whether to enable mark as solved button
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute(
                """
                INSERT INTO pph_post_assist_config(
                    forum_id,
                    enable_accept_solutions,
                    enable_mark_as_solved
                ) VALUES ($1, $2, $3)
            """,
                forum_id,
                enable_accept_solutions,
                enable_mark_as_solved,
            )

            config = await conn.fetchrow(
                """
                SELECT * FROM pph_post_assist_config
                WHERE forum_id = $1;
            """,
                forum_id,
            )

            for entity_id, entity_type in entities:
                await conn.execute(
                    """
                    INSERT INTO pph_post_assist_tags(
                        configuration_id,
                        entity_id,
                        entity_type
                    ) VALUES ($1, $2, $3)
                """,
                    config["id"],
                    entity_id,
                    entity_type,
                )

            await conn.execute(
                """
                INSERT INTO pph_post_assist_tag_message(
                    configuration_id,
                    custom_message
                ) VALUES ($1, $2)
            """,
                config["id"],
                entity_tag_message,
            )

            await conn.execute(
                """
                INSERT INTO pph_post_assist_reply(
                    configuration_id,
                    custom_message
                ) VALUES ($1, $2)
            """,
                config["id"],
                reply,
            )

    async def update_configuration(
        self,
        id: int,
        forum_id: int,
        entities: list[tuple[int, str]],
        entity_tag_message: str,
        reply: str,
        enable_accept_solutions: bool | None = None,
        enable_mark_as_solved: bool | None = None,
    ):
        """Updates a configuration to the database.

        :param id: The configuration id to update
        :param entities: The entities to add
        :param entity_tag_message: The tag message
        :param reply: The reply message
        :param enable_accept_solutions: Enable accept solutions app command
        :param enable_mark_as_solved: Whether to enable mark as solved button
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            config = await self.get_config(id)

            if not config:
                return

            await conn.execute(
                """
                UPDATE pph_post_assist_config SET
                    forum_id = $1,
                    enable_accept_solutions = COALESCE($3, enable_accept_solutions),
                    enable_mark_as_solved = COALESCE($4, enable_mark_as_solved)
                WHERE id = $2;
                """,
                forum_id,
                id,
                enable_accept_solutions,
                enable_mark_as_solved,
            )

            await conn.execute(
                """
                DELETE FROM pph_post_assist_tags WHERE configuration_id = $1;
            """,
                id,
            )

            for entity_id, entity_type in entities:
                await conn.execute(
                    """
                    INSERT INTO pph_post_assist_tags(
                        configuration_id,
                        entity_id,
                        entity_type
                    ) VALUES ($1, $2, $3)
                """,
                    config["id"],
                    entity_id,
                    entity_type,
                )

            await conn.execute(
                """
                UPDATE pph_post_assist_tag_message SET
                    custom_message = $1
                WHERE configuration_id = $2;
            """,
                entity_tag_message,
                config["id"],
            )

            await conn.execute(
                """
                UPDATE pph_post_assist_reply SET
                    custom_message = $1
                WHERE configuration_id = $2;
            """,
                reply,
                config["id"],
            )

    async def delete_configuration(self, id: int):
        """Deletes a configuration from the database.

        :param id: The configuration id to delete
        """

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute(
                """
                DELETE FROM pph_post_assist_config WHERE id = $1;
            """,
                id,
            )

    async def is_mark_as_solution_enabled(self, forum_id: int):
        """Checks if the mark as solution is enabled for a forum."""

        async with self._pool.acquire() as conn:
            conn: Pool

            res = await conn.fetchrow(
                """
                SELECT id, enable_accept_solutions
                FROM pph_post_assist_config
                WHERE forum_id = $1;
                """,
                forum_id,
            )

            if not res:
                return (-1, False)

            res = (int(res["id"]), bool(res["enable_accept_solutions"]))
            return res

    async def is_mark_as_solved_enabled_for_forum(self, forum_id: int):
        """Check if mark as solved button is enabled for a specific forum.

        :param forum_id: The forum ID
        :return: Tuple of (config_id, is_enabled)
        """
        async with self._pool.acquire() as conn:
            conn: Pool

            res = await conn.fetchrow(
                """
                SELECT id,
                       COALESCE(enable_mark_as_solved, FALSE)
                           as enable_mark_as_solved
                FROM pph_post_assist_config
                WHERE forum_id = $1;
                """,
                forum_id,
            )

            if not res:
                return (-1, False)

            return (int(res["id"]), bool(res["enable_mark_as_solved"]))

    async def get_mark_as_solved_tag(self, forum_id: int) -> int | None:
        """Get the forum tag used when marking a thread as solved."""

        async with self._pool.acquire() as conn:
            conn: Pool

            res = await conn.fetchrow(
                """
                SELECT tag_id
                FROM pph_post_assist_mark_as_solved_tags
                WHERE forum_id = $1;
                """,
                forum_id,
            )

            if res and res["tag_id"]:
                return int(res["tag_id"])

            return None

    async def set_mark_as_solved_tag(self, forum_id: int, tag_id: int) -> None:
        """Set/update the forum tag used when a thread is marked as solved."""

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute(
                """
                INSERT INTO pph_post_assist_mark_as_solved_tags(forum_id, tag_id)
                VALUES ($1, $2)
                ON CONFLICT (forum_id)
                DO UPDATE SET tag_id = EXCLUDED.tag_id;
                """,
                forum_id,
                tag_id,
            )

    async def delete_mark_as_solved_tag(self, forum_id: int) -> None:
        """Delete the forum tag mapping for mark-as-solved."""

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute(
                """
                DELETE FROM pph_post_assist_mark_as_solved_tags
                WHERE forum_id = $1;
                """,
                forum_id,
            )

    async def get_persistent_mark_as_solved_views(self):
        """Gets all active persistent mark-as-solved button views."""

        async with self._pool.acquire() as conn:
            conn: Pool

            views = await conn.fetch(
                """
                SELECT *
                FROM pph_post_assist_mark_as_solved_views
                WHERE closed = false;
                """
            )

        return views

    async def close_persistent_mark_as_solved_view(self, thread_id: int) -> None:
        """Mark a persistent mark-as-solved view as closed."""

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute(
                """
                UPDATE pph_post_assist_mark_as_solved_views
                SET closed = true
                WHERE thread_id = $1;
                """,
                thread_id,
            )

    async def add_persistent_mark_as_solved_view(
        self, thread_id: int, message_id: int, author_id: int
    ) -> None:
        """Store a persistent mark-as-solved view."""

        async with self._pool.acquire() as conn:
            conn: Pool

            await conn.execute(
                """
                INSERT INTO pph_post_assist_mark_as_solved_views (
                    thread_id,
                    message_id,
                    author_id
                )
                VALUES ($1, $2, $3)
                ON CONFLICT (thread_id)
                DO UPDATE SET
                    message_id = EXCLUDED.message_id,
                    author_id = EXCLUDED.author_id,
                    closed = false;
                """,
                thread_id,
                message_id,
                author_id,
            )

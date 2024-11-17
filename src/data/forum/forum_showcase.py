from datetime import datetime
from typing import Literal

from asyncpg import Pool
from logging import Logger


class ShowcaseForum(object):
    """Represents a forum that is showcased."""

    id: int
    forum_id: int
    showcase_id: int
    created_at: datetime

    def __init__(
        self,
        id: int,
        forum_id: int,
        showcase_id: int,
        created_at: datetime,
    ):
        self.id = id
        self.forum_id = forum_id
        self.showcase_id = showcase_id
        self.created_at = created_at


class AddShowcaseForum(object):
    """DTO for adding a forum to the showcase."""

    forum_id: int
    showcase_id: int

    def __init__(self, forum_id: int, showcase_id: int) -> None:
        self.forum_id = forum_id
        self.showcase_id = showcase_id


class ForumShowcase(object):
    """The showcase forum class that contains the showcase configuration."""

    id: int
    target_channel: int
    schedule: datetime
    interval: Literal["daily", "weekly", "monthly"]
    weekday: str
    forums: list[ShowcaseForum]
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        id: int,
        target_channel: int,
        schedule: datetime,
        interval: Literal["daily", "weekly", "monthly"],
        weekday: str,
        forums: list[ShowcaseForum],
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        self.id = id
        self.target_channel = target_channel
        self.schedule = schedule
        self.interval = interval
        self.weekday = weekday
        self.forums = forums
        self.created_at = created_at
        self.updated_at = updated_at

    def get_forum(self, id: int) -> ShowcaseForum | None:
        for forum in self.forums:
            if forum.id == id:
                return forum

        return

    def add_forum(self, forum: ShowcaseForum):
        self.forums.append(forum)

    def remove_forum(self, id: int) -> ShowcaseForum | None:
        for forum in self.forums:
            if forum.id == id:
                self.forums.remove(forum)
                return forum
        return


class UpdateForumShowcase(object):
    """The showcase forum class that contains the showcase configuration."""

    id: int
    target_channel: int
    schedule: datetime
    interval: Literal["daily", "weekly", "monthly"]
    weekday: str
    updated_at: datetime

    def __init__(
        self,
        id: int,
        target_channel: int,
        schedule: datetime,
        interval: Literal["daily", "weekly", "monthly"],
        weekday: str,
        updated_at: datetime,
    ) -> None:
        self.id = id
        self.target_channel = target_channel
        self.schedule = schedule
        self.interval = interval
        self.weekday = weekday
        self.updated_at = updated_at


class ForumShowcaseDB:
    """The database handler for Forum Showcase."""

    _pool: Pool
    logger: Logger

    def __init__(self, pool: Pool, logger: Logger) -> None:
        self._pool = pool
        self.logger = logger

    async def get_showcases(self) -> list[ForumShowcase]:
        async with self._pool.acquire() as conn:
            conn: Pool

            showcase_records = await conn.fetch("""
                SELECT * FROM pph_forum_showcase;
            """)
            showcases: list[ForumShowcase] = [
                ForumShowcase(
                    id=record["id"],
                    target_channel=record["target_channel"],
                    schedule=record["schedule"],
                    interval=record["interval"],
                    weekday=record["weekday"],
                    forums=[],
                    created_at=record["created_at"],
                    updated_at=record["updated_at"],
                )
                for record in showcase_records
            ]

            # TODO: use left join to get forums
            for showcase in showcases:
                showcase.forums = await self.get_forums(showcase.id)

            return showcases

    async def get_forums(self, showcase_id: int) -> list[ShowcaseForum]:
        async with self._pool.acquire() as conn:
            conn: Pool

            forums_records = await conn.fetch(
                """
                SELECT * FROM pph_forum_showcase_forum
                WHERE showcase_id = $1;
            """,
                showcase_id,
            )
            forums: list[ShowcaseForum] = [
                ShowcaseForum(
                    id=record["id"],
                    forum_id=record["forum_id"],
                    showcase_id=record["showcase_id"],
                    created_at=record["created_at"],
                )
                for record in forums_records
            ]

            return forums

    async def add_showcase(self, showcase: ForumShowcase) -> ForumShowcase:
        async with self._pool.acquire() as conn:
            conn: Pool

            try:
                await conn.execute(
                    """
                INSERT INTO pph_forum_showcase(
                    id,
                    target_channel,
                    schedule,
                    interval,
                    weekday,
                ) VALUES (
                    $1,
                    $2,
                    $3,
                    $4.
                    $5
                );
                """,
                    showcase.id,
                    showcase.target_channel,
                    showcase.schedule,
                    showcase.interval,
                    showcase.weekday,
                )

                return showcase
            except Exception as e:
                raise e

    async def add_forum(self, forum: AddShowcaseForum) -> ShowcaseForum:
        async with self._pool.acquire() as conn:
            conn: Pool

            try:
                record = await conn.fetchrow(
                    """
                    INSERT INTO pph_forum_showcase_forum(
                        forum_id, showcase_id
                    )
                    VALUES ($1, $2)
                    RETURNING *;
                """,
                    forum.forum_id,
                    forum.showcase_id,
                )

                showcase_forum = ShowcaseForum(
                    id=record["id"],
                    forum_id=record["forum_id"],
                    showcase_id=record["showcase_id"],
                    created_at=record["created_at"],
                )

                return showcase_forum
            except Exception as e:
                raise e

    async def delete_forum(self, id: int) -> bool:
        async with self._pool.acquire() as conn:
            conn: Pool

            try:
                await conn.execute(
                    """
                    DELETE FROM pph_forum_showcase_forum
                    WHERE id = $1
                    RETURNING *;
                """,
                    id,
                )

                return True
            except Exception:
                return False

    async def update_showcase(self, data: UpdateForumShowcase) -> bool:
        async with self._pool.acquire() as conn:
            conn: Pool

            try:
                await conn.execute(
                    """
                        UPDATE pph_forum_showcase
                        SET
                            target_channel = $1,
                            schedule = $2,
                            interval = $3,
                            weekday = $4,
                            updated_at = $5
                        WHERE id = $6;
                """,
                    data.target_channel,
                    data.schedule.replace(tzinfo=None),
                    data.interval,
                    data.weekday,
                    data.updated_at.replace(tzinfo=None),
                    data.id,
                )

                return True
            except Exception as e:
                self.logger.error(f"Failed to update showcase {data.id}: {str(e)}")
                return False

    async def delete_showcase(self, showcase__id: int) -> bool:
        async with self._pool.acquire() as conn:
            conn: Pool

            try:
                await conn.execute(
                    """
                    DELETE FROM pph_forum_showcase
                    WHERE id = $1
                """,
                    showcase__id,
                )

                return True
            except Exception:
                return False

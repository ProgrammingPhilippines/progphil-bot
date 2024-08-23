from asyncpg import Pool
from datetime import datetime
from typing import Literal


class ShowcaseForum(object):
    """Represents a forum that is showcased."""
    forum_id: int
    showcase_id: int
    created_at: datetime

    def __init__(self, forum_id: int, showcase_id: int, created_at: datetime):
        self.forum_id = forum_id
        self.showcase_id = showcase_id
        self.created_at = created_at


class ForumShowcase(object):
    """The showcase forum class that contains the showcase configuration."""
    id: int
    target_channel: int
    schedule: datetime
    interval: Literal["daily", "weekly", "monthly"]
    status: Literal["active", "inactive"]
    forums: list[ShowcaseForum]
    created_at: datetime
    updated_at: datetime

    def __init__(
            self,
            id: int,
            target_channel: int,
            schedule: datetime,
            interval: Literal["daily", "weekly", "monthly"],
            status: Literal["active", "inactive"],
            forums: list[ShowcaseForum],
            created_at: datetime,
            updated_at: datetime
    ) -> None:
        self.id = id
        self.target_channel = target_channel
        self.schedule = schedule
        self.interval = interval
        self.status = status
        self.forums = forums
        self.created_at = created_at
        self.updated_at = updated_at


class UpdateForumShowcase(object):
    """The showcase forum class that contains the showcase configuration."""
    id: int
    target_channel: int
    schedule: datetime
    interval: Literal["daily", "weekly", "monthly"]
    status: Literal["active", "inactive"]
    updated_at: datetime

    def __init__(
            self,
            id: int,
            target_channel: int,
            schedule: datetime,
            interval: Literal["daily", "weekly", "monthly"],
            status: Literal["active", "inactive"],
            updated_at: datetime
    ) -> None:
        self.id = id
        self.target_channel = target_channel
        self.schedule = schedule
        self.interval = interval
        self.status = status
        self.updated_at = updated_at


class ForumShowcaseDB:
    """The database handler for Forum Showcase."""
    _pool: Pool

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def get_showcases(self) -> list[ForumShowcase]:
        async with self._pool.acquire() as conn:
            conn: Pool

            showcases: list[ForumShowcase] = await conn.fetch("""
                SELECT * FROM forum_showcase;
            """)

            # TODO: use left join to get forums
            for showcase in showcases:
                showcase.forums = await self.get_forums(showcase.id)

            return showcases

    async def get_forums(self, showcase_id: int) -> list[ShowcaseForum]:
        async with self._pool.acquire() as conn:
            conn: Pool

            forums: list[ShowcaseForum] = await conn.fetch("""
                SELECT * FROM forum_showcase_forum
                WHERE showcase_id = $1;
            """, showcase_id)

            return forums

    async def add_showcase(self, showcase: ForumShowcase) -> ForumShowcase:
        async with self._pool.acquire() as conn:
            conn: Pool

            try:
                await conn.execute("""
                INSERT INTO forum_showcase(
                    id,
                    target_channel,
                    schedule,
                    interval,
                ) VALUES (
                    $1,
                    $2,
                    $3,
                    $4
                );
                """, showcase.id, showcase.target_channel, showcase.schedule, showcase.interval)

                return showcase
            except Exception as e:
                print(e)
                return None

    async def add_forum(
            self,
            forum: ShowcaseForum
            ) -> ShowcaseForum | None:
        async with self._pool.acquire() as conn:
            conn: Pool

            try:
                await conn.execute("""
                    INSERT INTO forum_showcase_forum(
                        forum_id, showcase_id
                    )
                    VALUES ($1, $2, $3);
                """, forum.forum_id, forum.showcase_id)

                return forum
            except Exception as e:
                print(e)
                return None

    async def delete_forum(self, forum_id: int) -> ShowcaseForum:
        async with self._pool.acquire() as conn:
            conn: Pool

            try:
                forum: ShowcaseForum = await conn.execute("""
                    DELETE FROM forum_showcase_forum
                    WHERE forum_id = $1
                    RETURNING *;
                """, forum_id)

                return forum
            except Exception as e:
                print(e)
                return None

    async def update_showcase(
            self,
            data: UpdateForumShowcase
    ) -> ForumShowcase:
        async with self._pool.acquire() as conn:
            conn: Pool

            try:
                updated_showcase: ForumShowcase = await conn.execute("""
                    UPDATE forum_showcase
                    SET
                        target_channel = $1,
                        schedule = $2,
                        interval = $3
                        updated_at = $4
                    WHERE id = $5
                    RETURNING *;
                """, data.target_channel, data.schedule, data.interval, data.updated_at, data.id)

                return updated_showcase
            except Exception as e:
                print(e)
                return None

    async def delete_showcase(self, showcase__id: int):
        async with self._pool.acquire() as conn:
            conn: Pool

            try:
                showcase: ForumShowcase = await conn.execute("""
                    DELETE FROM forum_showcase
                    WHERE id = $1
                    RETURNING *;
                """, showcase__id)

                return showcase
            except Exception as e:
                print(e)
                return None

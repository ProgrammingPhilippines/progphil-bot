from discord import Interaction, ForumChannel
from discord.ext.commands import GroupCog, Bot
from discord.app_commands import command
from src.utils.decorators import is_staff
from src.data.forum.forum_showcase import ForumShowcase, UpdateForumShowcase, ForumShowcaseDB
from logging import Logger
from datetime import datetime, timedelta
from typing import Literal
import asyncio


class ForumShowcaseCog(GroupCog):
    forum_showcases: list[ForumShowcase]
    tasks: dict[int, asyncio.Task]

    def __init__(self, bot: Bot):
        self.bot = bot
        self.forum_showcase_db = ForumShowcaseDB(self.bot.pool)
        self.logger: Logger = bot.logger
        self.forum_showcases: list[ForumShowcase] = None
        self.tasks = {}

    async def cog_load(self) -> None:
        asyncio.create_task(self.init_data())
        showcases = await self.forum_showcase_db.get_showcases()

        for showcase in showcases:
            schedule = showcase.schedule
            if not schedule:
                return

            self.logger.info(f"Starting showcase task for {showcase.id}")
            task = asyncio.create_task(self.schedule_showcase(showcase))
            self.tasks[showcase.id] = task

    async def schedule_showcase(self, showcase: ForumShowcase):
        # infinite loop until task is cancelled
        while True:
            if showcase.status == "inactive":
                self.logger.info(f"Showcase {showcase.id} is inactive, stopping task")
                return

            # TODO: if current time is not yet reached, wait until it is
            sleep_time = showcase.schedule - datetime.now()
            self.logger.info(f"Waiting {sleep_time.total_seconds()} seconds for showcase {showcase.id}")
            asyncio.sleep(sleep_time.total_seconds())

            for forum in showcase.forums:
                self.logger.info(f"Showing forum {forum.forum_id} in showcase {showcase.id}")
                await self.showcase_threads(forum)

            next_schedule = self._calculate_next_schedule(
                showcase.schedule,
                showcase.interval
            )
            update_showcase_schedule = UpdateForumShowcase(
                id=showcase.id,
                schedule=next_schedule,
                interval=showcase.interval,
                target_channel=showcase.target_channel,
                updated_at=datetime.now()
            )
            self.logger.info(f"Updating showcase {showcase.id} schedule to {next_schedule}")
            self.forum_showcase_db.update_showcase(update_showcase_schedule)
            showcase.schedule = next_schedule

    def _calculate_next_schedule(
            current_schedule: datetime,
            interval: Literal["daily", "weekly", "monthly"]
    ) -> datetime:
        if interval == "daily":
            return current_schedule + timedelta(days=1)

        if interval == "weekly":
            return current_schedule + timedelta(days=7)

        if interval == "monthly":
            return current_schedule + timedelta(days=30)

    async def showcase_threads(self, forum: ForumChannel):
        # TODO: select threads randomly
        pass

    async def cancel_task(self, task_id: int):
        if task_id not in self.tasks:
            return

        task = self.tasks.pop(task_id)
        _ = task.cancel()

    async def init_data(self):
        showcases = await self.forum_showcase_db.get_showcases()
        self.forum_showcases = showcases

    @is_staff()
    @command(
        name="add",
        description="Adds a forum to the showcase"
    )
    async def add_forum(self, interaction: Interaction):
        pass

    @is_staff()
    @command(
        name="list",
        description="List all forums to showcase."
    )
    async def list_forum(self, interaction: Interaction):
        pass

    @is_staff()
    @command(
        name="delete",
        description="Delete 1 or more forums from the showcase"
    )
    async def delete_forum(self, interaction: Interaction):
        pass

    @is_staff()
    @command(
        name="config",
        description="Configure the schedule of a forum."
    )
    async def config(self, interaction: Interaction):
        pass

    @is_staff()
    @command(
        name="toggle",
        description="Enable/Disable the showcase feature."
    )
    async def toggle(self, interaction: Interaction):
        pass


async def setup(bot: Bot):
    await bot.add_cog(ForumShowcase(bot))

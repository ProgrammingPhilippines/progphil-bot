import asyncio
import random
import threading
from datetime import datetime
from logging import Logger
from typing import Literal

from dateutil.relativedelta import relativedelta
from discord import Interaction, Thread
from discord.app_commands import command
from discord.ext.commands import Bot, GroupCog
from discord.ext.tasks import loop

from src.data.admin.config_auto import Config
from src.data.forum.forum_showcase import (
    ForumShowcase,
    ForumShowcaseDB,
    UpdateForumShowcase,
)
from src.ui.views.forum_showcase import ForumShowcaseAddView
from src.utils.decorators import is_staff


class ForumShowcaseCog(GroupCog, name="forum_showcase"):
    forum_showcase: dict[int, ForumShowcase]
    tasks: dict[int, threading.Thread]

    def __init__(self, bot: Bot):
        self.bot = bot
        self.forum_showcase_db = ForumShowcaseDB(self.bot.pool)
        self.db_config = Config(self.bot.pool)
        self.logger: Logger = bot.logger
        self.forum_showcase: ForumShowcase = {}

    async def cog_load(self) -> None:
        await asyncio.create_task(self.init_data())

        schedule = self.forum_showcase.schedule

        if not schedule:
            return

        self.logger.info(f"Scheduling forum showcase {self.forum_showcase.id}")
        self.schedule_showcase.change_interval(hours=schedule.hour)
        self.schedule_showcase.start()

    @loop()
    async def schedule_showcase(self):
        config = await self.db_config.get_config("forum_showcase")

        if not config["config_status"]:
            return

        showcase = self.forum_showcase

        if showcase.status == "inactive":
            self.logger.info(f"Showcase {showcase.id} is inactive, stopping task")
            return

        try:
            await self.showcase_threads(showcase)
        except Exception as e:
            self.logger.info(f"Error in showcase_threads for {showcase.id}: {e}")

        next_schedule = self._calculate_next_schedule(
            showcase.schedule, showcase.interval
        )
        update_showcase_schedule = UpdateForumShowcase(
            id=showcase.id,
            schedule=next_schedule,
            interval=showcase.interval,
            target_channel=showcase.target_channel,
            status=showcase.status,
            updated_at=datetime.now(),
        )

        await self.forum_showcase_db.update_showcase(update_showcase_schedule)
        self.logger.info(
            f"forum showcase {showcase.id} is scheduled to run on {next_schedule}"
        )
        showcase.schedule = next_schedule

    def _calculate_next_schedule(
        self,
        current_schedule: datetime,
        interval: Literal["daily", "weekly", "monthly"],
    ) -> datetime:
        if interval == "daily":
            return current_schedule + relativedelta(days=1)

        if interval == "weekly":
            return current_schedule + relativedelta(weeks=1)

        if interval == "monthly":
            return current_schedule + relativedelta(months=1)

    async def showcase_threads(self, forum_showcase: ForumShowcase):
        self.logger.info(f"target channel id: {forum_showcase.target_channel}")
        target_channel = await self.bot.fetch_channel(forum_showcase.target_channel)

        if target_channel is None:
            self.logger.info(
                f"target channel not found: {forum_showcase.target_channel}"
            )
            return

        self.logger.info(f"target channel: {target_channel}")
        msgs = ""

        for showcase_forum in forum_showcase.forums:
            forum = self.bot.get_channel(showcase_forum.forum_id)

            if not forum:
                continue

            threads = forum.threads
            total_threads = len(threads)

            if total_threads == 0:
                continue

            thread = random.choice(threads)
            msg = self._build_response(forum.name, thread)
            msgs += msg + "\n"

        # build message
        message = f"""
            Hey, everyone! You might wanna check out these posts from our forums

            {msgs}
        """
        await target_channel.send(message)

    def _build_response(self, forum_name: str, thread: Thread):
        return f"""
        ### {forum_name}
        {thread.mention}
        """

    async def init_data(self):
        data = await self.forum_showcase_db.get_showcases()
        showcase = data[0]

        self.forum_showcase = showcase

    @is_staff()
    @command(name="add", description="Adds a forum to the showcase")
    async def add_forum(self, interaction: Interaction):
        # since we only have one showcase, we can just use 1 as the id
        # that was added in the database during migration
        forum_showcase_id = 1
        existing_forums = await self.forum_showcase_db.get_forums(forum_showcase_id)
        existing_selections = [
            self.bot.get_channel(forum.forum_id) for forum in existing_forums
        ]
        forum_showcase_add_view = ForumShowcaseAddView(
            existing_forums=existing_selections,
            forum_showcase_id=forum_showcase_id,
            forum_showcase_db=self.forum_showcase_db,
            logger=self.logger,
        )

        await interaction.response.send_message(
            "Select the forums you want to showcase",
            view=forum_showcase_add_view,
            ephemeral=True,
        )
        await forum_showcase_add_view.wait()

        forum_showcase = self.forum_showcase
        for forums in forum_showcase_add_view.showcase_forums:
            forum_showcase.forums.append(forums)

    @is_staff()
    @command(name="list", description="List all forums to showcase.")
    async def list_forum(self, interaction: Interaction):
        self.logger.info(f"Forum Showcase: {self.forum_showcase.id}")

        forum_showcase = self.forum_showcase

        await interaction.response.send_message(
            f"Forums to showcase: {forum_showcase.forums}"
        )

    @is_staff()
    @command(name="delete", description="Delete 1 or more forums from the showcase")
    async def delete_forum(self, interaction: Interaction):
        pass

    @is_staff()
    @command(name="config", description="Configure the schedule of a forum.")
    async def config(self, interaction: Interaction):
        pass

    @is_staff()
    @command(name="toggle", description="Enable/Disable the showcase feature.")
    async def toggle(self, interaction: Interaction):
        pass


async def setup(bot: Bot):
    await bot.add_cog(ForumShowcaseCog(bot))

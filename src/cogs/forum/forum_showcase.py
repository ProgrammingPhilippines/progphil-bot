import asyncio
import random
import threading
from datetime import datetime
from logging import Logger
from typing import Literal

from dateutil.relativedelta import relativedelta
from discord import Interaction, Thread, app_commands
from discord.app_commands import command
from discord.ext.commands import Bot, GroupCog
from discord.ext.tasks import loop

from src.data.admin.config_auto import Config
from src.data.forum.forum_showcase import (
    ForumShowcase,
    ForumShowcaseDB,
    ShowcaseForum,
    UpdateForumShowcase,
)
from src.utils.decorators import is_staff


class ForumShowcaseCog(GroupCog, name="forum_showcase"):
    forum_showcase: dict[int, ForumShowcase]
    tasks: dict[int, threading.Thread]
    first_load: bool

    def __init__(self, bot: Bot):
        self.bot = bot
        self.forum_showcase_db = ForumShowcaseDB(self.bot.pool)
        self.db_config = Config(self.bot.pool)
        self.logger: Logger = bot.logger
        self.forum_showcase: ForumShowcase = {}

    async def cog_load(self) -> None:
        self.first_load = True
        await asyncio.create_task(self.init_data())

        schedule = self.forum_showcase.schedule

        if not schedule:
            return

        self.schedule_showcase.start()

    @loop()
    async def schedule_showcase(self):
        config = await self.db_config.get_config("forum_showcase")

        if not config["config_status"]:
            return

        if self.first_load:
            self.refresh_loop_interval()
            self.first_load = False
            return

        showcase = self.forum_showcase

        if showcase.status == "inactive":
            self.logger.info(f"Showcase {showcase.id} is inactive, stopping task")
            return

        try:
            await self.showcase_threads(showcase)
        except Exception as e:
            self.logger.info(f"Error in showcase_threads for {showcase.id}: {e}")

        await self.update_schedule()
        self.schedule_showcase.restart()

    async def update_schedule(self):
        showcase = self.forum_showcase
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

    def refresh_loop_interval(self):
        time = self.forum_showcase.schedule - datetime.now()
        hours = time.total_seconds() // 3600.0
        self.logger.info(
            f"Scheduling forum showcase {self.forum_showcase.id}, {hours} hours from now"
        )
        self.schedule_showcase.change_interval(hours=hours)

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
        target_channel = self.bot.get_channel(forum_showcase.target_channel)

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
            msgs += msg

        # build message
        message = f"# Hey, everyone! You might wanna check out these posts from our forums\n{msgs}"
        await target_channel.send(message)

    def _build_response(self, forum_name: str, thread: Thread):
        return f"### {forum_name}\n{thread.mention}\n"

    async def init_data(self):
        data = await self.forum_showcase_db.get_showcases()
        showcase = data[0]

        self.forum_showcase = showcase

    @is_staff()
    @command(name="add", description="Adds a forum to the showcase")
    async def add_forum(
        self,
        interaction: Interaction,
        forum: str,
    ):
        # since we only have one showcase, we can just use 1 as the id
        # that was added in the database during migration
        forum_showcase_id = 1
        selected_forum = interaction.guild.get_channel(int(forum))

        now = datetime.now()
        showcase_forum = ShowcaseForum(
            forum_id=selected_forum.id,
            showcase_id=forum_showcase_id,
            created_at=now,
        )

        try:
            await self.forum_showcase_db.add_forum(showcase_forum)
        except Exception as e:
            self.logger.error(
                f"Failed to add forum {showcase_forum.forum_id} to showcase.\n {e}"
            )
            await interaction.response.send_message(
                f"Failed to add forum {showcase_forum.forum_id} to showcase.",
                ephemeral=True,
            )
            return

        forum_showcase = self.forum_showcase
        forum_showcase.forums.append(showcase_forum)
        await interaction.response.send_message(
            f"Added {selected_forum.mention} to showcase.", ephemeral=True
        )

    @add_forum.autocomplete("forum")
    async def add_forum_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        existing_forums = [forum.forum_id for forum in self.forum_showcase.forums]
        forums = interaction.guild.forums

        return [
            app_commands.Choice(name=forum.name, value=str(forum.id))
            for forum in forums
            if current.lower() in forum.name.lower() and forum.id not in existing_forums
        ][:25]  # Discord limits autocomplete to 25 choices

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

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
    AddShowcaseForum,
    ForumShowcase,
    ForumShowcaseDB,
    UpdateForumShowcase,
)
from src.utils.decorators import is_staff


class ForumShowcaseCog(GroupCog, name="forum_showcase"):
    forum_showcase_id: int
    forum_showcase: dict[int, ForumShowcase]
    tasks: dict[int, threading.Thread]
    first_load: bool

    def __init__(self, bot: Bot):
        self.bot = bot
        self.forum_showcase_db = ForumShowcaseDB(self.bot.pool)
        self.db_config = Config(self.bot.pool)
        self.logger: Logger = bot.logger
        self.forum_showcase_id = 1
        self.forum_showcase: ForumShowcase = {}

    async def cog_load(self) -> None:
        self.first_load = True
        await asyncio.create_task(self.init_data())

        schedule = self.forum_showcase.schedule

        if not schedule:
            return

        config = await self.db_config.get_config("forum_showcase")

        if not config["config_status"]:
            return

        self.schedule_showcase.start()

    @loop()
    async def schedule_showcase(self):
        forum_showcase = self.forum_showcase
        config = await self.db_config.get_config("forum_showcase")

        if not config["config_status"]:
            self.logger.info(f"Showcase {forum_showcase.id} is inactive, stopping task")
            return

        if self.first_load:
            await self.refresh_loop_interval()
            self.first_load = False
            return

        try:
            await self.showcase_threads(forum_showcase)
        except Exception as e:
            self.logger.info(f"Error in showcase_threads for {forum_showcase.id}: {e}")

        await self.update_schedule()
        await self.refresh_loop_interval()

    async def update_schedule(self):
        forum_showcase = self.forum_showcase
        next_schedule = self._calculate_next_schedule(
            forum_showcase.schedule, forum_showcase.interval
        )
        update_showcase_schedule = UpdateForumShowcase(
            id=forum_showcase.id,
            schedule=next_schedule,
            interval=forum_showcase.interval,
            target_channel=forum_showcase.target_channel,
            updated_at=datetime.now(),
        )

        await self.forum_showcase_db.update_showcase(update_showcase_schedule)
        self.logger.info(
            f"forum showcase {forum_showcase.id} is scheduled to run on {next_schedule}"
        )
        forum_showcase.schedule = next_schedule

    async def refresh_loop_interval(self):
        now = datetime.now()
        diff = self.forum_showcase.schedule - now

        # if the time is negative, it means the showcase has already passed
        if diff.total_seconds() <= 0:
            next_sched = datetime.now()
            next_sched = next_sched.replace(
                hour=self.forum_showcase.schedule.hour,
                minute=self.forum_showcase.schedule.minute,
                second=0,
            )

            next_sched = self._calculate_next_schedule(
                next_sched, self.forum_showcase.interval
            )

            self.logger.info(
                f"forum showcase {self.forum_showcase.id} is scheduled to run on {next_sched}"
            )

            diff = next_sched - now

        self.logger.info(
            f"forum showcase {self.forum_showcase.id}, will rerun on {diff}."
        )
        seconds = diff.total_seconds()
        self.schedule_showcase.change_interval(seconds=seconds)

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
        try:
            selected_forum = interaction.guild.get_channel(int(forum))

            if self.forum_showcase.get_forum(selected_forum.id) is not None:
                await interaction.response.send_message(
                    f"Forum {selected_forum.name} is already in the showcase"
                )
                return

            showcase_forum = AddShowcaseForum(
                forum_id=selected_forum.id,
                showcase_id=self.forum_showcase_id,
            )

            result = await self.forum_showcase_db.add_forum(showcase_forum)
            self.logger.info(result)

            self.forum_showcase.add_forum(result)
            await interaction.response.send_message(
                f"Added {selected_forum.mention} to showcase.", ephemeral=True
            )
        except Exception as e:
            self.logger.error(
                f"Failed to add forum {showcase_forum.forum_id} to showcase.\n {e}"
            )
            await interaction.response.send_message(
                f"Failed to add forum {showcase_forum.forum_id} to showcase.",
                ephemeral=True,
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
    async def delete_forum(self, interaction: Interaction, id: int):
        try:
            if self.forum_showcase.get_forum(id) is None:
                await interaction.response.send_message(
                    f"Forum with id {id} is not in the showcase", ephemeral=True
                )
                return

            await self.forum_showcase_db.delete_forum(id)
            await interaction.response.send_message(
                f"Forum {id} has been removed from the forum showcase.",
                ephemeral=True,
            )
            self.forum_showcase.remove_forum(id)
            self.logger.info(f"total forums: {len(self.forum_showcase.forums)}")
        except Exception as e:
            self.logger.info(e)
            await interaction.response.send_message(f"Failed to delete forum {id}")

    @delete_forum.autocomplete("id")
    async def delete_forum_autocomplete(
        self, interaction: Interaction, current: str | None
    ) -> list[app_commands.Choice[str]]:
        if current == "" or current is None:
            return [
                app_commands.Choice(name=forum.id, value=str(forum.id))
                for forum in self.forum_showcase.forums
            ][:25]  # Discord limits autocomplete to 25 choices

        return [
            app_commands.Choice(name=forum.id, value=str(forum.id))
            for forum in self.forum_showcase.forums
            if current.lower() in str(forum.id)
        ][:25]  # Discord limits autocomplete to 25 choices

    @is_staff()
    @command(name="config", description="Configure the schedule of a forum.")
    async def config(self, interaction: Interaction):
        pass

    @is_staff()
    @command(name="toggle", description="Enable/Disable the showcase feature.")
    async def toggle(self, interaction: Interaction):
        status = await self.db_config.toggle_config("forum_showcase")

        if status:
            self.schedule_showcase.start()
            is_running = self.schedule_showcase.is_running()
            self.logger.info(f"Forum showcase is now enabled={is_running}")
            await interaction.response.send_message(
                "Forum showcase is now enabled.", ephemeral=True
            )
            return

        self.schedule_showcase.cancel()
        self.logger.info("Forum showcase is now disabled")
        await interaction.response.send_message(
            "Forum showcase is now disabled.", ephemeral=True
        )


async def setup(bot: Bot):
    await bot.add_cog(ForumShowcaseCog(bot))

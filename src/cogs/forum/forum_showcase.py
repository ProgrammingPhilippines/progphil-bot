import asyncio
import random
import threading
from datetime import datetime
from logging import Logger
from typing import Literal

from dateutil.relativedelta import relativedelta
from discord import (
    ButtonStyle,
    Embed,
    Interaction,
    SelectOption,
    TextChannel,
    Thread,
    app_commands,
)

from discord.app_commands import command
from discord.ext.commands import Bot, GroupCog
from discord.ext.tasks import loop
from discord.ui import Button, Select, View

from src.data.admin.config_auto import Config
from src.data.forum.forum_showcase import (
    AddShowcaseForum,
    ForumShowcase,
    ForumShowcaseDB,
    UpdateForumShowcase,
)
from src.utils.decorators import is_staff

SCHEDULES = [
    "12 AM",
    "01 AM",
    "02 AM",
    "03 AM",
    "04 AM",
    "05 AM",
    "06 AM",
    "07 AM",
    "08 AM",
    "09 AM",
    "10 AM",
    "11 AM",
    "12 PM",
    "01 PM",
    "02 PM",
    "03 PM",
    "04 PM",
    "05 PM",
    "06 PM",
    "07 PM",
    "08 PM",
    "09 PM",
    "10 PM",
    "11 PM",
]


class ForumShowcaseCog(GroupCog, name="forum-showcase"):
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

        if not schedule or not self.forum_showcase.target_channel:
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
            self.refresh_loop_interval()
            self.first_load = False
            return

        try:
            await self.showcase_threads(forum_showcase)
        except Exception as e:
            self.logger.info(f"Error in showcase_threads for {forum_showcase.id}: {e}")

        await self.update_schedule()
        self.refresh_loop_interval()

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

    def refresh_loop_interval(self):
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
            current_schedule = current_schedule.replace(day=1)
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

            # filter the threads that is posted on current month
            current_month = datetime.now().month
            current_year = datetime.now().year
            threads = [
                thread
                for thread in forum.threads
                if thread.created_at.month == current_month
                and thread.created_at.year == current_year
            ]

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
    ):
        async def selection_callback(interaction: Interaction):
            await interaction.response.send_message("Thanks!", ephemeral=True)
            view.stop()

        async def cancel_callback(interaction: Interaction):
            await interaction.response.send_message("Cancelled!", ephemeral=True)
            view.stop()
            return

        selected_forums = self.forum_showcase.forums

        view = View(timeout=400)
        cancel = Button(label="Cancel", style=ButtonStyle.red)
        cancel.callback = cancel_callback

        selection = Select(placeholder="Select a forum to add")
        selection.callback = selection_callback

        forum_ids = interaction.guild.forums

        # filter the already selected forums
        options = [
            forum
            for forum in forum_ids
            if forum.id not in [forum.forum_id for forum in selected_forums]
        ]

        if len(options) == 0:
            await interaction.response.send_message(
                "No more forums to add!", ephemeral=True
            )
            return

        for forum in options:
            selection.add_option(
                label=forum.name,
                value=forum.id,
            )

        view.add_item(selection)
        view.add_item(cancel)

        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()

        if not selection.values:
            view.stop()
            await interaction.followup.send("No selected forums.", ephemeral=True)
            return

        selected_forum = selection.values[0]
        forum = self.bot.get_channel(int(selected_forum))
        showcase_forum = AddShowcaseForum(
            forum_id=forum.id,
            showcase_id=self.forum_showcase_id,
        )

        try:
            result = await self.forum_showcase_db.add_forum(showcase_forum)
            self.forum_showcase.add_forum(result)

            await interaction.followup.send(
                f"Added {forum.mention} to showcase.", ephemeral=True
            )
        except Exception:
            await interaction.followup.send(
                f"Failed to add forum {forum.mention} to showcase.",
                ephemeral=True,
            )

    @is_staff()
    @command(name="list", description="List all forums to showcase.")
    async def list_forum(self, interaction: Interaction):
        forum_showcase = self.forum_showcase

        embed = Embed(
            title="Forum Showcase",
            description="List of forums to showcase.",
            color=0x00FF00,
            timestamp=interaction.created_at,
        )
        embed.set_author(
            name=self.bot.user.display_name,
            icon_url=self.bot.user.display_avatar,
        )

        for forum in forum_showcase.forums:
            forum_channel = self.bot.get_channel(forum.forum_id)
            embed = embed.add_field(
                name=f"**Forum**: {forum_channel.mention}",
                value=f"""
                **ID**: {forum.id}
                **Added at**: {forum.created_at.date()}
                """,
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

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
        selected_schedule = None
        selected_channel_id = None

        async def schedule_callback(interaction: Interaction):
            nonlocal selected_schedule
            selected_schedule = schedule_select.values[0]
            await interaction.response.defer()

        async def channel_callback(interaction: Interaction):
            nonlocal selected_channel_id
            selected_channel_id = int(channel_select.values[0])
            await interaction.response.defer()

        async def submit_callback(interaction: Interaction):
            if selected_schedule:
                self.forum_showcase.schedule = self._parse_schedule(selected_schedule)
                await self.update_schedule()
                self.refresh_loop_interval()
                await interaction.response.send_message(
                    f"Schedule updated to {selected_schedule}", ephemeral=True
                )

            if selected_channel_id:
                self.forum_showcase.target_channel = selected_channel_id
                channel = self.bot.get_channel(selected_channel_id)
                await interaction.response.send_message(
                    f"Target channel set to {channel.mention}", ephemeral=True
                )

            if not selected_schedule and not selected_channel_id:
                await interaction.response.send_message(
                    "No changes were made.", ephemeral=True
                )

            view.stop()

        async def cancel_callback(interaction: Interaction):
            await interaction.response.send_message(
                "Configuration cancelled", ephemeral=True
            )
            view.stop()

        view = View(timeout=300)

        schedule_select = Select(
            placeholder="Select a schedule",
            options=[SelectOption(label=s, value=s) for s in SCHEDULES],
        )
        schedule_select.callback = schedule_callback

        channel_select = Select(
            placeholder="Select a target channel",
            options=[
                SelectOption(label=channel.name, value=str(channel.id))
                for channel in interaction.guild.channels
                if isinstance(channel, TextChannel)
            ],
        )
        channel_select.callback = channel_callback

        submit_button = Button(label="Submit", style=ButtonStyle.green)
        submit_button.callback = submit_callback

        cancel_button = Button(label="Cancel", style=ButtonStyle.red)
        cancel_button.callback = cancel_callback

        view.add_item(schedule_select)
        view.add_item(channel_select)
        view.add_item(submit_button)
        view.add_item(cancel_button)

        await interaction.response.send_message(
            "Configure forum showcase:", view=view, ephemeral=True
        )

    def _parse_schedule(self, schedule: str) -> datetime:
        split = schedule.split(" ")
        hr_schedule = int(split[0])
        if split[1] == "PM" and hr_schedule != 12:
            hr_schedule += 12
        elif split[1] == "AM" and hr_schedule == 12:
            hr_schedule = 0
        return datetime.now().replace(hour=hr_schedule, minute=0, second=0)

    @is_staff()
    @command(name="toggle", description="Enable/Disable the showcase feature.")
    async def toggle(self, interaction: Interaction):
        status = await self.db_config.toggle_config("forum_showcase")

        if status:
            self.refresh_loop_interval()
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

import asyncio
import random
from datetime import datetime, timedelta, timezone
from logging import Logger
from math import floor

from dateutil.relativedelta import relativedelta
from discord import (
    ButtonStyle,
    Embed,
    Interaction,
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
from src.ui.views.forum_showcase import (
    ConfigureChannel,
    ConfigureTime,
    ConfigureWeekday,
)
from src.utils.decorators import is_staff

# List of hours from 12:00 AM to 11:00 PM
SCHEDULES = [
    f"{(hour + 12 if hour == 0 else hour) if hour < 12 else (hour if hour == 12 else hour - 12):02d} {'AM' if hour < 12 else 'PM'}"
    for hour in range(24)
]

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class ForumShowcaseCog(GroupCog, name="forum-showcase"):
    forum_showcase_id: int
    forum_showcase: ForumShowcase

    def __init__(self, bot: Bot):
        self.bot = bot
        self.forum_showcase_db = ForumShowcaseDB(self.bot.pool, self.bot.logger)  # type: ignore
        self.db_config = Config(self.bot.pool)  # type: ignore
        self.logger: Logger = bot.logger  # type: ignore
        self.forum_showcase_id = 1
        self.forum_showcase = {}  # type: ignore

    async def cog_load(self) -> None:
        await asyncio.create_task(self.init_data())

        schedule = self.forum_showcase.schedule
        target_channel = self.forum_showcase.target_channel

        if not schedule or not target_channel:
            return

        config = await self.db_config.get_config("forum_showcase")

        if not config["config_status"]:
            self.logger.info("[FORUM-SHOWCASE] Showcase is disabled")
            return

        self.schedule_showcase.start()

    @loop()
    async def schedule_showcase(self):
        config = await self.db_config.get_config("forum_showcase")

        if not config["config_status"]:
            self.logger.info("[FORUM-SHOWCASE] Showcase is inactive, stopping task")
            return

        now = datetime.now(timezone.utc)
        scheduled_time = self.forum_showcase.schedule.replace(tzinfo=timezone.utc)
        diff = floor((scheduled_time - now).total_seconds())

        # We need to current time is the same as the scheduled time,
        # because sometimes the this task runs halfway the schedule time
        # due to oversleeping.
        # If it happens, we need to reschedule the task
        if diff < 0:
            try:
                await self.showcase_threads(self.forum_showcase)
                self.logger.info("[FORUM-SHOWCASE] Showcase completed, rescheduling")
            except Exception as e:
                self.logger.error(f"[FORUM-SHOWCASE] Error in showcase_threads: {e}")
        else:
            pass

        await self.schedule_next_run()

    async def update_schedule(self, next_schedule: datetime):
        now = datetime.now(timezone.utc)
        update_showcase_schedule = UpdateForumShowcase(
            id=self.forum_showcase.id,
            schedule=next_schedule,
            interval=self.forum_showcase.interval,
            target_channel=self.forum_showcase.target_channel,
            weekday=self.forum_showcase.weekday,
            updated_at=now,
        )

        await asyncio.create_task(
            self.forum_showcase_db.update_showcase(update_showcase_schedule)
        )

        self.forum_showcase.schedule = next_schedule

    async def schedule_next_run(self, run_now=False):
        if not self.forum_showcase:
            self.logger.error("[FORUM-SHOWCASE] No forum showcase configured")
            return

        next_run = self.calculate_next_run()

        now = datetime.now(timezone.utc)
        diff = (next_run - now).total_seconds()

        self.logger.info(f"[FORUM-SHOWCASE] New showcase schedule: {next_run}")

        await self.update_schedule(next_run)

        if diff > 0 or run_now:
            self.schedule_showcase.change_interval(seconds=max(1, diff))
        else:
            self.logger.info(
                "[FORUM-SHOWCASE] Next run time is in the past. Waiting for next interval."
            )

    def calculate_next_run(self) -> datetime:
        now = datetime.now(timezone.utc)
        schedule = self.forum_showcase.schedule
        interval = self.forum_showcase.interval

        next_run = schedule.replace(
            year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc
        )

        while next_run <= now:
            if interval == "daily":
                next_run += relativedelta(days=1)
            elif interval == "weekly":
                weekday = WEEKDAYS.index(self.forum_showcase.weekday)
                next_run += relativedelta(day=now.day + 1, weekday=weekday)
            elif interval == "monthly":
                next_month = next_run.replace(day=1) + relativedelta(months=1)
                next_month_day = (next_month + relativedelta(days=1)).day
                next_run = next_month.replace(day=min(schedule.day, next_month_day))

        return next_run

    async def showcase_threads(self, forum_showcase: ForumShowcase):
        self.logger.info(
            f"[FORUM-SHOWCASE] target channel id: {forum_showcase.target_channel}"
        )
        target_channel = self.bot.get_channel(forum_showcase.target_channel)

        if target_channel is None:
            self.logger.info(
                f"[FORUM-SHOWCASE] target channel not found: {forum_showcase.target_channel}"
            )
            return

        self.logger.info(f"[FORUM-SHOWCASE] target channel: {target_channel}")
        msgs = []

        for showcase_forum in forum_showcase.forums:
            forum = self.bot.get_channel(showcase_forum.forum_id)

            if not forum:
                continue

            now = datetime.now(timezone.utc)
            current_month = now.month
            current_year = now.year

            # filter the threads that is not archived
            # and is posted on current month
            threads = [
                thread
                for thread in forum.threads  # type: ignore
                if thread.created_at.month == current_month  # type: ignore
                and thread.created_at.year == current_year  # type: ignore
                and not thread.archived
            ]

            total_threads = len(threads)

            if total_threads == 0:
                continue

            random.seed(now.timestamp())
            thread = random.choice(threads)
            msgs.append(f"### {forum.name}\n{thread.mention}\n")  # type: ignore

        if msgs:
            message = f"# Hey, everyone! You might wanna check out these posts from our forums\n{''.join(msgs)}"
            await target_channel.send(message)  # type: ignore
        else:
            self.logger.info("[FORUM-SHOWCASE] No threads found for the current month.")

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
                value=str(forum.id),
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
            self.logger.info(
                f"[FORUM-SHOWCASE] total forums: {len(self.forum_showcase.forums)}"
            )
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
        await interaction.response.defer()
        target_channel_select = ConfigureChannel(
            self.forum_showcase,
            self.forum_showcase_id,
            self.forum_showcase_db,
            self.logger,
        )

        await interaction.followup.send(
            "Select a target channel", view=target_channel_select, ephemeral=True
        )
        await target_channel_select.wait()

        self.forum_showcase = target_channel_select.forum_showcase

        weekday_select = ConfigureWeekday(
            self.forum_showcase, self.forum_showcase_db, self.logger
        )

        await interaction.followup.send(
            "Select a weekday", view=weekday_select, ephemeral=True
        )
        await weekday_select.wait()

        self.forum_showcase = weekday_select.forum_showcase

        time_select = ConfigureTime(
            self.forum_showcase, self.forum_showcase_db, self.logger
        )
        await interaction.followup.send(
            "Select a time", view=time_select, ephemeral=True
        )
        await time_select.wait()

        self.forum_showcase = time_select.forum_showcase

        await self.schedule_next_run()

        await interaction.followup.send(
            "All settings have been updated.", ephemeral=True
        )

    def _parse_schedule(self, schedule: str) -> datetime:
        split = schedule.split(" ")
        hr_schedule = int(split[0])

        if split[1] == "PM" and hr_schedule != 12:
            hr_schedule += 12
        elif split[1] == "AM" and hr_schedule == 12:
            hr_schedule = 0

        # need to convert from UTC+08:00 to UTC+00:00 to match the timezone where the bot is running
        utc_8 = datetime.now().replace(
            hour=hr_schedule, minute=0, second=0, tzinfo=timezone(timedelta(hours=8))
        )
        parsed_schedule = (utc_8 - timedelta(hours=8)).replace(tzinfo=timezone.utc)

        return parsed_schedule

    @is_staff()
    @command(name="toggle", description="Enable/Disable the showcase feature.")
    async def toggle(self, interaction: Interaction):
        status = await self.db_config.toggle_config("forum_showcase")

        if status:
            next_run = self.calculate_next_run()
            await self.schedule_next_run()

            if not self.schedule_showcase.is_running():
                self.schedule_showcase.start()

            await interaction.response.send_message(
                f"Forum showcase is now enabled. Next run scheduled for {next_run.strftime('%Y-%m-%d %H:%M:%S')}.",
                ephemeral=True,
            )
            return

        if self.schedule_showcase.is_running():
            self.schedule_showcase.cancel()

        self.logger.info("[FORUM-SHOWCASE] Forum showcase is now disabled")
        await interaction.response.send_message(
            "Forum showcase is now disabled.", ephemeral=True
        )


async def setup(bot: Bot):
    await bot.add_cog(ForumShowcaseCog(bot))

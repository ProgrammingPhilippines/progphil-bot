from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Literal

from discord import Button, ButtonStyle, ChannelType, Interaction, SelectOption
from discord.ui import ChannelSelect, Select, View, button, select

from src.data.forum.forum_showcase import (
    ForumShowcase,
    ForumShowcaseDB,
    UpdateForumShowcase,
)

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

INTERVAL = ["daily", "weekly", "monthly"]


class ConfigureChannel(View):
    def __init__(
        self,
        forum_showcase: ForumShowcase,
        forum_showcase_id: int,
        forum_showcase_db: ForumShowcaseDB,
        logger: Logger,
    ):
        super().__init__(timeout=300)
        self.forum_showcase = forum_showcase
        self.forum_showcase_id = forum_showcase_id
        self.forum_showcase_db = forum_showcase_db
        self.logger = logger
        self.selected_channel: int | None = None

    @button(label="Skip", style=ButtonStyle.red, custom_id="cancel-channel-select")  # type: ignore
    async def cancel_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_message("Skipped!", ephemeral=True)
        self.stop()

    @button(label="Submit", style=ButtonStyle.green, custom_id="submit-channel-select")  # type: ignore
    async def submit_button(self, interaction: Interaction, button: Button):
        if self.selected_channel is None:
            await interaction.response.send_message(
                "No changes were made for the target channel.", ephemeral=True
            )
            self.stop()
            return

        channel = interaction.guild.get_channel(self.selected_channel)  # type: ignore

        if channel is None:
            await interaction.response.send_message("Selected channel does not exist.")
            return self.stop()

        now = datetime.now(timezone.utc)

        update_showcase = UpdateForumShowcase(
            id=self.forum_showcase_id,
            target_channel=channel.id,  # type: ignore
            schedule=self.forum_showcase.schedule,
            interval=self.forum_showcase.interval,
            weekday=self.forum_showcase.weekday,
            updated_at=now,
        )

        await self.forum_showcase_db.update_showcase(update_showcase)

        await interaction.response.send_message(
            f"New target channel is {channel.mention}, id {channel.id}",  # type: ignore
            ephemeral=True,
        )
        self.logger.info(
            f"[FORUM-SHOWCASE] Updated target channel to {channel.mention}"  # type: ignore
        )
        self.stop()

    @select(
        cls=ChannelSelect,
        placeholder="Select a target channel",
        channel_types=[ChannelType.text],
    )
    async def channel_select(self, interaction: Interaction, selection: ChannelSelect):
        selected_channel = selection.values[0] or None
        if selected_channel is not None:
            self.selected_channel = selected_channel.id
            self.forum_showcase.target_channel = self.selected_channel
        await interaction.response.defer()

class ConfigureInterval(View):
    def __init__(self,
        forum_showcase: ForumShowcase,
        forum_showcase_db: ForumShowcaseDB,
        logger: Logger,
    ):
        super().__init__(timeout=300)
        self.forum_showcase = forum_showcase
        self.forum_showcase_db = forum_showcase_db
        self.logger = logger
        self.selected_interval: str | None = None

    @button(label="Skip", style=ButtonStyle.red, custom_id="cancel-interval-select")  # type: ignore
    async def cancel_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_message("Skipped!", ephemeral=True)
        self.stop()

    @button(label="Submit", style=ButtonStyle.green, custom_id="submit-interval-select") # type: ignore
    async def submit_button(self, interaction: Interaction, button: Button):
        if self.selected_interval is None:
            await interaction.response.send_message(
                "No changes were made for the interval.", ephemeral=True
            )
            self.stop()
            return

        now = datetime.now(timezone.utc)
        update_showcase = UpdateForumShowcase(
            id=self.forum_showcase.id,
            target_channel=self.forum_showcase.target_channel,
            schedule=self.forum_showcase.schedule,
            interval=str(self.selected_interval),
            weekday=self.forum_showcase.weekday,
            updated_at=now,
        )
        await self.forum_showcase_db.update_showcase(update_showcase)

        await interaction.response.send_message(
            f"New interval is {self.selected_interval}", ephemeral=True
        )
        self.stop()

    @select(
        cls=Select,
        placeholder="Select an interval",
        options=[
            SelectOption(
                label=interval,
                value=interval,
            )
            for interval in INTERVAL
        ],
    )
    async def select_interval(self, interaction: Interaction, selection: Select):
        selected_interval = selection.values[0] or None
        if selected_interval is not None:
            self.selected_interval = selected_interval
            self.forum_showcase.interval = self.selected_interval
        await interaction.response.defer()

class ConfigureWeekday(View):
    def __init__(
        self,
        forum_showcase: ForumShowcase,
        forum_showcase_db: ForumShowcaseDB,
        logger: Logger,
    ):
        super().__init__(timeout=300)
        self.forum_showcase = forum_showcase
        self.forum_showcase_db = forum_showcase_db
        self.logger = logger
        self.selected_weekday: str | None = None

    @button(label="Skip", style=ButtonStyle.red)  # type: ignore
    async def cancel_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_message("Skipped!", ephemeral=True)
        self.stop()

    @button(label="Submit", style=ButtonStyle.green)  # type: ignore
    async def submit_button(self, interaction: Interaction, button: Button):
        if self.selected_weekday is None:
            await interaction.response.send_message(
                "No changes were made for the weekday.", ephemeral=True
            )
            self.stop()
            return

        now = datetime.now(timezone.utc)
        update_showcase = UpdateForumShowcase(
            id=self.forum_showcase.id,
            target_channel=self.forum_showcase.target_channel,
            schedule=self.forum_showcase.schedule,
            interval=self.forum_showcase.interval,
            weekday=self.selected_weekday,
            updated_at=now,
        )
        await self.forum_showcase_db.update_showcase(update_showcase)

        await interaction.response.send_message(
            f"New weekday is {self.selected_weekday}", ephemeral=True
        )
        self.stop()

    @select(
        cls=Select,
        placeholder="Select a weekday",
        options=[
            SelectOption(
                label=weekday,
                value=weekday,
            )
            for weekday in WEEKDAYS
        ],
    )
    async def weekday_select(self, interaction: Interaction, selection: Select):
        selected_weekday = selection.values[0] or None
        if selected_weekday is not None:
            self.selected_weekday = selected_weekday
            self.forum_showcase.weekday = self.selected_weekday
        await interaction.response.defer()


class ConfigureTime(View):
    def __init__(
        self,
        forum_showcase: ForumShowcase,
        forum_showcase_db: ForumShowcaseDB,
        logger: Logger,
    ):
        super().__init__(timeout=300)
        self.forum_showcase = forum_showcase
        self.forum_showcase_db = forum_showcase_db
        self.logger = logger
        self.selected_time: str | None = None

    @button(label="Skip", style=ButtonStyle.red)  # type: ignore
    async def cancel_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_message("Skipped!", ephemeral=True)
        self.stop()

    @button(label="Submit", style=ButtonStyle.green)  # type: ignore
    async def submit_button(self, interaction: Interaction, button: Button):
        if self.selected_time is None:
            await interaction.response.send_message(
                "No changes were made for the time.", ephemeral=True
            )
            self.stop()
            return

        now = datetime.now(timezone.utc)
        update_showcase = UpdateForumShowcase(
            id=self.forum_showcase.id,
            target_channel=self.forum_showcase.target_channel,
            schedule=self.forum_showcase.schedule,
            interval=self.forum_showcase.interval,
            weekday=self.forum_showcase.weekday,
            updated_at=now,
        )

        await self.forum_showcase_db.update_showcase(update_showcase)

        await interaction.response.send_message(
            f"New time is {self.selected_time}", ephemeral=True
        )
        self.stop()

    @select(
        cls=Select,
        placeholder="Select a time",
        options=[
            SelectOption(
                label=hour,
                value=hour,
            )
            for hour in SCHEDULES
        ],
    )
    async def time_select(self, interaction: Interaction, selection: Select):
        selected_time = selection.values[0]
        if selected_time is not None:
            self.selected_time = selected_time
            parsed_schedule = parse_schedule(self.selected_time)
            schedule = parsed_schedule.replace(day=self.forum_showcase.schedule.day)
            self.forum_showcase.schedule = schedule
        await interaction.response.defer()


def parse_schedule(schedule: str) -> datetime:
    split = schedule.split(" ")
    hr_schedule = int(split[0])

    if split[1] == "PM" and hr_schedule != 12:
        hr_schedule += 12
    elif split[1] == "AM" and hr_schedule == 12:
        hr_schedule = 0

    # need to convert from UTC+08:00 to UTC+00:00 to match the timezone
    # where the bot is running
    now = datetime.now(timezone(timedelta(hours=8)))
    parsed_schedule = now.replace(
        hour=hr_schedule,
        minute=0,
        second=0,
        microsecond=0,
    )
    parsed_schedule = (parsed_schedule - timedelta(hours=8)).replace(tzinfo=timezone.utc)

    return parsed_schedule

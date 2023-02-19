import json
from datetime import datetime, time, timedelta
from typing import Type

import requests
import discord
from discord.ext import tasks
from discord.ext.commands import Bot, Cog
from discord.app_commands import command, describe

from database.trivia import TriviaDB
from config import API
from utils.decorators import is_staff


class Trivia(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db: Type[TriviaDB | None] = None
        self.config: Type[dict | None] = None
        self.trivia_loop.start()

    async def cog_load(self) -> None:
        self.db = TriviaDB(self.bot.pool)
        self.config = await self.db.get_config()

    @staticmethod
    def get_schedule(config) -> time:
        """
        Gets the schedule of the trivia

        :return: Time
        """

        if config is None:  # If the config is None, return 00:00
            return time(hour=12, minute=0, second=0)

        schedule_utc_plus_8 = datetime.strptime(
            config["schedule"],
            "%H:%M").time()  # Converts the schedule to a time object

        schedule_with_day = datetime.combine(
            datetime.today(),
            schedule_utc_plus_8)  # Combines the schedule with the current day

        schedule = schedule_with_day - timedelta(hours=8)  # Converts the schedule to UTC+0

        return schedule.time()

    @tasks.loop(time=time(16, 0, 0))  # Runs every day at 00:00 UTC+8 (default)
    async def trivia_loop(self) -> None:

        if self.config is None:  # If the config is None, return
            return

        response = requests.get(
            "https://api.api-ninjas.com/v1/facts",
            headers={
                "X-Api-Key": API.api_ninja
            }
        )

        if response.status_code != 200:  # If the status code is not 200, return
            await self.trivia_channel.send(
                f"An error occurred while fetching trivia. Error code: {response.status_code}"
            )
            return

        trivia_channel = self.bot.get_channel(self.config["channel_id"])
        await trivia_channel.send()

    @command(name="test", description="Test command")
    async def test(self, interaction: discord.Interaction, t: int):
        await interaction.response.send_message(json.dumps(self.config, indent=4))

    @is_staff()
    @command(name="trivia_schedule", description="Schedule the trivia session")
    @describe(schedule="Schedule of the trivia in 24 hour format ex. 12:00")
    async def trivia_schedule(self, interaction: discord.Interaction, schedule: str) -> None:
        """
        Schedules a trivia session

        :param interaction: Interaction
        :param schedule: Schedule of the trivia
        """

        if self.config is None:
            await interaction.response.send_message(
                "Please setup the trivia first, use /trivia_setup.",
                ephemeral=True)
            return

        await self.db.update_config(
            channel_id=self.config["channel_id"],
            schedule=schedule
        )

        self.trivia_loop.change_interval(
            time=self.get_schedule(self.config)
        )  # Changes the interval of the trivia loop

        await self.bot.reload_extension("bot.cogs.trivia")

        await interaction.response.send_message(
            "Trivia session scheduled",
            ephemeral=True
        )

    @is_staff()
    @command(name="trivia_channel", description="Set the trivia channel")
    @describe(channel="Channel to send the trivia to")
    async def trivia_channel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        """
        Sets the trivia channel

        :param interaction: Interaction
        :param channel: Channel to send the trivia to
        """

        if self.config is None:
            await interaction.response.send_message(
                "Please setup the trivia first, use /trivia_setup.",
                ephemeral=True)
            return

        await self.db.update_config(
            channel_id=channel.id,
            schedule=self.config["schedule"]
        )

        await self.bot.reload_extension("bot.cogs.trivia")

        await interaction.response.send_message(
            "Trivia channel set",
            ephemeral=True
        )

    @is_staff()
    @command(name="trivia_setup", description="Setup the trivia")
    @describe(channel="Channel to send the trivia to")
    @describe(schedule="Schedule of the trivia session in 24 hour format ex. 12:00")
    async def trivia_setup(self, interaction: discord.Interaction, channel: discord.TextChannel, schedule: str) -> None:
        """
        Sets up the trivia

        :param interaction: Interaction
        :param channel: Channel to send the trivia to
        :param schedule: Schedule of the trivia
        """
        if self.config is not None:  # This makes that the trivia can only be setup once
            await interaction.response.send_message(
                "Trivia is already setup, use /trivia_channel and /trivia_schedule to change the channel and schedule.",
                ephemeral=True)
            return

        self.db.insert_config(
            channel_id=channel.id,
            schedule=schedule
        )

        self.trivia_loop.change_interval(
            time=self.get_schedule(self.config)
        )  # Changes the interval of the trivia loop

        await self.bot.reload_extension("bot.cogs.trivia")

        await interaction.response.send_message(
            "Trivia setup",
            ephemeral=True
        )


async def setup(bot: Bot):
    await bot.add_cog(Trivia(bot))

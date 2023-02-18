import datetime
from typing import Type

import requests
import discord
from discord.ext import tasks
from discord.ext.commands import Bot, Cog
from discord.app_commands import command, describe

from config import API
from utils.decorators import is_staff


class Trivia(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.trivia_channel: Type[discord.TextChannel | None] = None
        self.trivia_schedule: Type[datetime.time | None] = None

    @tasks.loop(minutes=1)
    async def trivia_loop(self):
        if self.trivia_channel is None:
            return
        await self.trivia_channel.send("test")

    @is_staff()
    @command(name="trivia_schedule", description="Schedule the trivia session")
    @describe(schedule="Schedule of the trivia session")
    async def trivia_schedule(self, interaction: discord.Interaction, schedule: str) -> None:
        """
        Schedules a trivia session

        :param interaction: Interaction
        :param schedule: Schedule of the trivia session
        """
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
        self.trivia_channel = channel
        await interaction.response.send_message(
            "Trivia channel set",
            ephemeral=True
        )

    @is_staff()
    @command(name="trivia_start", description="Start the trivia session")
    async def trivia_start(self, interaction: discord.Interaction) -> None:
        """
        Starts a trivia session

        :param interaction: Interaction
        """
        await interaction.response.send_message(
            "Trivia session started",
            ephemeral=True
        )
        self.trivia_loop.start()


async def setup(bot: Bot):
    await bot.add_cog(Trivia(bot))

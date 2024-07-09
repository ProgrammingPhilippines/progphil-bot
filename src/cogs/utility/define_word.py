from typing import List, Tuple

import requests
import discord
from discord import Embed
from discord.ext.commands import (
    Context,
    GroupCog,
    command as prefixed_command
)
from discord.app_commands import command

from src.data.admin.config_auto import Config
from src.ui.views.define_word import DefineWordPagination
from src.utils.decorators import is_staff
from discord.ext.commands import Bot


class Define(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Config(self.bot.pool)

    @prefixed_command(
        usage="<word>",
        help="Define a Word (e.g. define hello)"
    )
    async def define(
            self,
            ctx: Context,
            word: str,
    ):
        """
        Give Dictionary Definition to the Given Word

        :param word: The Word to Define
        :param ctx: The Context of the Command
        """

        config = await self.config.get_config("define_word")

        if not config["config_status"]:
            await ctx.send("Sorry, this command is currently disabled.")
            return

        url = "https://api.dictionaryapi.dev/api/v2/entries/en/" + word
        response = requests.get(url)

        if not response.ok:
            message = f"Could not find definition for {word.lower()}"
            respond_message = Embed(
                description=message,
                color=discord.Color.blurple()
            )

            return await ctx.send(embed=respond_message)

        data = response.json()

        if "title" in data and data["title"] == "No Definitions Found":
            message = data['message']
            respond_message = Embed(
                title=word,
                description=message,
                color=discord.Color.blurple()
            )
            await ctx.send(embed=respond_message)
            return

        data = self._format_data(data)
        part_of_speech, definition = data[0]

        embed = Embed()
        embed.title = f"Definition for {word.lower()}"
        embed.description = f"`[{part_of_speech.upper()}]` - {definition}"

        view = DefineWordPagination(word.lower(), ctx.author, data)

        await ctx.send(embed=embed, view=view)

    @is_staff()
    @command(name="toggle", description="Toggle the define word command.")
    async def toggle_config(self, interaction: discord.Interaction):
        """Toggles converter."""

        toggle_map = {
            True: "ON",
            False: "OFF"
        }
        toggle = await self.config.toggle_config("define_word")
        await interaction.response.send_message(
            f"Turned {toggle_map[toggle]} Define Word.",
            ephemeral=True
        )

    @staticmethod
    def _format_data(data: List[dict]) -> List[Tuple[str, str]]:
        formatted_data = []

        while data:
            temp = data.pop()
            for meaning in temp["meanings"]:
                for definition in meaning["definitions"]:
                    formatted_data.append((meaning["partOfSpeech"], definition["definition"]))

        return formatted_data


async def setup(bot: Bot):
    await bot.add_cog(Define(bot))

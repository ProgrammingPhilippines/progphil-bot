import requests
import discord
from discord import Embed
from discord.ext.commands import (
    Bot,
    Context,
    GroupCog,
    command as prefixed_command
)
from discord.app_commands import command

from bot.database.config_auto import Config
from bot.ui.views.define_word import DefineWordPagination
from bot.utils.decorators import is_staff


class Define(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Config(self.bot.pool)

    @prefixed_command()
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

        config = await self.config.get_config("currency_converter")

        if not config["config_status"]:
            await ctx.send("Sorry, this command is currently disabled.")
            return

        url = "https://api.dictionaryapi.dev/api/v2/entries/en/" + word
        response = requests.get(url)

        if not response.ok:
            message = f"Could not find definition for {word}"
            respond_message = Embed(
                title=word,
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

        view = DefineWordPagination(ctx.author, data)

        embed = Embed()
        embed.title = f"Definition for {word}"
        part_of_speech = data[0]["meanings"][0]["partOfSpeech"]
        definition = data[0]["meanings"][0]["definitions"][0]["definition"]

        embed.description = f"({part_of_speech}) - {definition}"
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


async def setup(bot: Bot):
    await bot.add_cog(Define(bot))

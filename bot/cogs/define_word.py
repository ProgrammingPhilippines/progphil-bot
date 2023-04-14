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

from bot.ui.views.define_word import DefineWordPagination
from bot.utils.decorators import is_staff


class Define(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.command_enabled = True

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

        if not self.command_enabled:
            await ctx.send("Sorry, this command is currently disabled.", delete_after=10)
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
    @command(name="toggle", description="Turn Define Command On/Off")
    async def toggle(
            self,
            interaction: discord.Interaction,
    ) -> None:
        """
        Turn Define Command On/Off

        :param interaction: Interaction
        """

        if self.command_enabled:
            self.command_enabled = False
            response = "Command is now Disabled"
        else:
            self.command_enabled = True
            response = "Command is now Enabled"

        await interaction.response.send_message(response, ephemeral=True)


async def setup(bot: Bot):
    await bot.add_cog(Define(bot))

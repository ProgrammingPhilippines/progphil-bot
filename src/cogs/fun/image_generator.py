from typing import List, Tuple

import requests
import discord
from bs4 import BeautifulSoup
from discord import Embed
from discord.ext.commands import Bot, Context, GroupCog, command as prefixed_command
from discord.app_commands import command

from src.data.admin.config_auto import Config
# from src.ui.views.define_word import DefineWordPagination
from src.utils.decorators import is_staff


class ImageGen(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Config(self.bot.pool)

    @prefixed_command(
        usage="<word>", help="Generate a random image (e.g. rphoto coding)"
    )
    async def rphoto(
        self,
        ctx: Context,
        word: str,
    ):
        """
        Generate Random Image based on Criteria

        :param word: The Image Criteria
        :param ctx: The Context of the Command
        """

        config = await self.config.get_config("image_gen")

        if not config["config_status"]:
            await ctx.send("Sorry, this command is currently disabled.")
            return

        url = "https://source.unsplash.com/random/?{}".format(word)
        response = requests.get(url, allow_redirects=False)

        if not response.ok:
            message = f"Could not generate image for {word.lower()}"
            respond_message = Embed(description=message, color=discord.Color.blurple())

            return await ctx.send(embed=respond_message)

        data = response.content
        img = self.get_href(data)

        await ctx.send(f"Here's your generated image for criteria:\n[{word}]({img})")

    @is_staff()
    @command(name="toggle", description="Toggle the define word command.")
    async def toggle_config(self, interaction: discord.Interaction):
        """Toggles converter."""

        toggle_map = {True: "ON", False: "OFF"}
        toggle = await self.config.toggle_config("image_gen")
        await interaction.response.send_message(
            f"Turned {toggle_map[toggle]} Image Generator", ephemeral=True
        )

    @staticmethod
    def get_href(body):
        soup = BeautifulSoup(body, "html.parser")
        link = soup.find("a", href=True)
        return link["href"]


async def setup(bot: Bot):
    await bot.add_cog(ImageGen(bot))

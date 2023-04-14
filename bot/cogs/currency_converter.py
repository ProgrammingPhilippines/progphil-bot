import requests
import discord
from discord.ui import Button, View
from discord import Embed
from discord.ext.commands import (
    Bot,
    Context,
    GroupCog,
    command as prefixed_command
)
from discord.app_commands import command

from bot.database.config_auto import Config
from bot.config import GuildInfo
from bot.utils.decorators import is_staff


class Convert(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Config(self.bot.pool)
        symbols = requests.get("https://api.exchangerate.host/symbols").json()["symbols"]
        self.symbols = [(symbol, symbols[symbol]["description"]) for symbol in symbols]

    @prefixed_command()
    async def exchange(
            self,
            ctx: Context,
            amount: float,
            from_currency: str,
            to_currency: str,
    ) -> None:
        """
        Convert Currency

        :param ctx: The Context of the Command
        :param amount: The Amount to Convert
        :param from_currency: The Currency to Convert From
        :param to_currency: The Currency to Convert To
        """
        config = await self.config.get_config("currency_converter")

        if not config["config_status"]:
            await ctx.send("Sorry, this command is currently disabled.", delete_after=10)
            return

        if not self._is_supported(from_currency):
            await ctx.send(f"Sorry, {from_currency.upper()} is not supported.")
            return

        if not self._is_supported(to_currency):
            await ctx.send(f"Sorry, {to_currency.upper()} is not supported.")
            return

        response = requests.get(
            f"https://api.exchangerate.host/convert?from={from_currency}&to={to_currency}&amount={amount}"
        )

        data = response.json()

        if response.status_code != 200 or not data["success"]:
            channel = self.bot.get_channel(GuildInfo.log_channel)
            await channel.send(f"An error occurred in the currency converter:\n```{data}```")
            await ctx.send("Sorry, I could not convert that currency.")
            return

        converted_amount = data["result"]

        await ctx.send(
            f"The exchange rate for {amount:.2f} {from_currency.upper()} is {converted_amount:.2f} {to_currency.upper()}."
        )

    @is_staff()
    @command(name="toggle", description="Toggle the currency converter command.")
    async def toggle_config(self, interaction: discord.Interaction):
        """Toggles auto tagging."""

        toggle_map = {
            True: "ON",
            False: "OFF"
        }
        toggle = await self.config.toggle_config("currency_converter")
        await interaction.response.send_message(
            f"Turned {toggle_map[toggle]} Auto Tagging.",
            ephemeral=True
        )

    def _is_supported(self, currency: str) -> bool:
        """
        Checks if the currency is supported

        :param currency: The currency to check
        :return:
        """
        return currency.upper() in [symbol[0] for symbol in self.symbols]


async def setup(bot: Bot) -> None:
    await bot.add_cog(Convert(bot))
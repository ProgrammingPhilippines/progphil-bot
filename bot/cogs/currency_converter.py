import requests
import discord
import locale
from discord import Embed
from discord.ext.commands import (
    Bot,
    Context,
    GroupCog,
    command as prefixed_command
)
from discord.app_commands import command

from database.config_auto import Config
from config import GuildInfo
from ui.views.currency_converter import CurrencyConverterPagination
from utils.decorators import is_staff


class Converter(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Config(self.bot.pool)
        symbols = requests.get("https://api.exchangerate.host/symbols").json()["symbols"]
        self.symbols = [(symbol, symbols[symbol]["description"]) for symbol in symbols]

    def is_valid(self, amount: str):
        return amount.isdigit() or amount.count(".") == 1
    
    def get_locale_code(self, currency_code):
        # Iterate through available locales and try to find a match
        for loc in locale.locale_alias:
            try:
                locale.setlocale(locale.LC_ALL, loc)
                info = locale.localeconv()
                if info['int_curr_symbol'] == currency_code:
                    return loc
            except:
                continue
        return None

    def format_currency(self, amount, currency_code):
        currency_code = currency_code.upper()
        locale_name = self.get_locale_code(currency_code)

        if locale_name is None:
            locale_name = "en-US"

        try:
            locale.setlocale(locale.LC_ALL, f'{locale_name}.UTF-8')
        except locale.Error:
            return ValueError(f"Locale '{locale_name}' is not available on this system.")

        # Remove currency symbol
        locale.__override_localeconv = {"currency_symbol": ""}

        # Format the amount as currency without the currency symbol
        formatted_currency = locale.currency(amount, symbol=False, grouping=True)

        return f'{formatted_currency} {currency_code}'

    @prefixed_command(
        usage="<amount> <from_currency> <to_currency>",
        help="Convert Currency to Another Currency (e.g. 10 usd eur)"
    )
    async def exchange(
            self,
            ctx: Context,
            amount: str,
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
        if not self.is_valid(amount) or len(amount) > 10:
            await ctx.send("Please enter a valid amount.")
            return

        config = await self.config.get_config("currency_converter")

        if not config["config_status"]:
            await ctx.send("Sorry, this command is currently disabled.")
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

        formatted_from = self.format_currency(float(amount), from_currency)
        formatted_to = self.format_currency(converted_amount, to_currency)

        await ctx.send(
            f"The exchange rate for {formatted_from} is {formatted_to}."
        )

    @prefixed_command(usage="<currency>", help="Get a list of supported currencies.")
    async def currencies(
            self,
            ctx: Context,
    ) -> None:
        """
        Get a list of supported currencies

        :param ctx: The Context of the Command
        """
        config = await self.config.get_config("currency_converter")

        if not config["config_status"]:
            await ctx.send("Sorry, this command is currently disabled.")
            return

        embed = Embed()
        embed.title = "Here are the available currencies:"
        embed.description = "\n".join(
            [f"{symbol[0].upper()} - {symbol[1]}" for count, symbol in enumerate(self.symbols, start=1) if count <= 10]
        )

        view = CurrencyConverterPagination(ctx.author, self.symbols)
        await ctx.send(embed=embed, view=view)

    @is_staff()
    @command(name="toggle", description="Toggle the currency converter command.")
    async def toggle_config(self, interaction: discord.Interaction):
        """Toggles converter."""

        toggle_map = {
            True: "ON",
            False: "OFF"
        }
        toggle = await self.config.toggle_config("currency_converter")
        await interaction.response.send_message(
            f"Turned {toggle_map[toggle]} Currency Converter.",
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
    await bot.add_cog(Converter(bot))

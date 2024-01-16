import traceback

from discord import Interaction
from discord.ext.commands import (
    Bot,
    Cog,
    CheckFailure as CtxCheckFailure,
    CommandError,
    CommandNotFound,
    Context,
    BadArgument,
    MissingRequiredArgument,
    UnexpectedQuoteError,
    InvalidEndOfQuotedStringError,
)
from discord.app_commands import (
    AppCommandError,
    CheckFailure,
    MissingRole,
    MissingPermissions,
    CommandOnCooldown,
)

from config import GuildInfo

error_map = {
    MissingRole: "You are missing the role {error.missing_role} to use this command.",
    MissingPermissions: "You are missing the required permissions to use this command.",
    CheckFailure: "You are not allowed to use this command.",
    CommandNotFound: "This command was not found.",
    CommandOnCooldown: (
        "This command is on cooldown. Try again in {error.retry_after:.2f} seconds."
    ),
    BadArgument: "Invalid argument passed correct usage:\n```{ctx.command.usage}```",
    MissingRequiredArgument: "Missing required argument:\n```{ctx.command.usage}```",
}  # note: some of these errors are not yet implemented in the bot


class ErrorHandler(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.error_message = "An error occurred."
        bot.tree.error(coro=self.__dispatch_to_app_command_handler)

    async def __dispatch_to_app_command_handler(
        self, interaction: Interaction, error: AppCommandError
    ):
        self.bot.dispatch("app_command_error", interaction, error)

    @Cog.listener()
    async def on_app_command_error(self, interaction: Interaction, error: CommandError):
        """
        Handles all errors that occur in app commands and sends a response to the user.

        :param interaction: Interaction
        :param error: Error
        """

        log_channel = self.bot.get_channel(GuildInfo.log_channel)

        error_message = error_map.get(
            type(error), self.error_message
        )  # gets the error message from the error map

        if type(error) not in error_map:
            trace = "".join(
                traceback.format_exception(None, error, error.__traceback__)
            )
            await log_channel.send(
                f"An error occurred in the app command handler:\n```{error}```"
            )
            await log_channel.send(f"Traceback:\n```{trace[:1950]}```")

        error_message = error_message.format(
            error=error
        )  # formats the error message if it has a format string

        if interaction.response.is_done():
            await interaction.followup.send(error_message, ephemeral=True)
        else:
            await interaction.response.send_message(error_message, ephemeral=True)

    @Cog.listener()
    async def on_command_error(self, ctx: Context, error: CommandError):
        """
        Handles all errors that occur in commands and sends a response to the user.

        :param ctx: Context
        :param error: Error
        """

        if isinstance(
            error,
            (
                UnexpectedQuoteError,
                InvalidEndOfQuotedStringError,
                CtxCheckFailure,
            ),
        ):
            return

        log_channel = self.bot.get_channel(GuildInfo.log_channel)
        error_message = error_map.get(type(error), self.error_message)

        if type(error) not in error_map:
            trace = "".join(
                traceback.format_exception(None, error, error.__traceback__)
            )

            await log_channel.send(
                f"An error occurred in the command handler:\n```{error}```"
            )
            await log_channel.send(f"Traceback:\n```{trace[:1950]}```")

        error_message = error_message.format(error=error, ctx=ctx)

        await ctx.send(error_message, delete_after=5)


async def setup(bot: Bot):
    await bot.add_cog(ErrorHandler(bot))

from typing import Union

from discord import Interaction
from discord.app_commands import (
    AppCommandError,
    CheckFailure,
    MissingRole,
    MissingPermissions,
    CommandNotFound,
    CommandOnCooldown
)
from discord.ext.commands import (
    Bot,
    Cog,
    CommandError,
)


class ErrorHandler(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.error_message = "An error occurred."
        bot.tree.error(coro=self.__dispatch_to_app_command_handler)

    async def __dispatch_to_app_command_handler(self, interaction: Interaction, error: AppCommandError):
        self.bot.dispatch("app_command_error", interaction, error)

    @Cog.listener()
    async def on_app_command_error(self, interaction: Interaction, error: CommandError):
        error_message = self.error_message

        try:
            raise error

        except CheckFailure as e:
            if isinstance(e, MissingRole):
                error_message = f"You are missing the role {', '.join(e.missing_role)} to use this command."
            elif isinstance(e, MissingPermissions):
                error_message = "You are missing the required permissions to use this command."
            elif isinstance(e, CommandOnCooldown):
                error_message = f"This command is on cooldown. Try again in {e.retry_after:.2f} seconds."
            else:
                error_message = "You are not allowed to use this command."

        except CommandNotFound:
            error_message = "This command was not found."

        finally:
            await interaction.response.send_message(error_message, ephemeral=True)


async def setup(bot: Bot):
    await bot.add_cog(ErrorHandler(bot))

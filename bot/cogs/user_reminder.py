import discord
from discord.app_commands import command, describe
from discord.ext.commands import Bot, GroupCog

from bot.utils.decorators import is_staff
from bot.database.config_auto import Config
from bot.database.user_reminder import UserReminderDB


class UserReminder(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Config(self.bot.pool)
        self.db = UserReminderDB(self.bot.pool)

    @is_staff()
    @command(name="toggle", description="Toggle the user reminder")
    async def toggle(self, interaction: discord.Interaction) -> None:
        """
        Toggles the trivia.
        """

        toggle_map = {
            True: "ON",
            False: "OFF"
        }
        config = "user_reminder"

        if not await self.config.get_config(config):
            await self.config.add_config(config)

        toggle = await self.config.toggle_config(config)

        await interaction.response.send_message(
            f"Turned {toggle_map[toggle]} User Reminder.",
            ephemeral=True
        )

    @is_staff()
    @command(name="setup", description="Setup the user reminder")
    @describe(message="Message to be sent to the user. To link a channel use <#channel_id>")
    async def setup(self, interaction: discord.Interaction, message: str) -> None:
        """
        Setup the user reminder
        """
        await self.db.insert(message)

        await interaction.response.send_message(
            "User Reminder setup complete.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(UserReminder(bot))

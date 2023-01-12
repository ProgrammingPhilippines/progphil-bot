import io
import discord
import requests
from discord.ext.commands import Bot, Cog
from discord.app_commands import command, describe, checks

ALLOWED_EXT = ["gif", "png", "jpeg", "jpg"]
REQUIRED_ROLES = [
    "Admin",
    "Moderator",
    "Helper",
    "baby, ako na lang kasi"
]
# might be exploited


class Announcements(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    # Add announcement commands here
    @command(
        name="media_announce",
        description="Send a announcement with media",
    )
    @describe(
        photo="The Photo File",
        to_announce="Message to announce"
    )
    @checks.has_any_role(
        *REQUIRED_ROLES
    )
    async def announce_with_media(
            self,
            interaction: discord.Interaction,
            photo: discord.Attachment,
            to_announce: str,
    ) -> None:
        channel = self.bot.get_channel(interaction.channel_id)
        await channel.send(to_announce, file=await photo.to_file())


async def setup(bot: Bot):
    await bot.add_cog(Announcements(bot))

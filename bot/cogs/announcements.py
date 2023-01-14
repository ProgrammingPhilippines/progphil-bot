from typing import Optional

import discord
from discord.ext.commands import Bot, Cog
from discord.app_commands import command, describe, checks

from utils.modals import Announcement
from utils.decorators import is_staff


ALLOWED_EXT = ["gif", "png", "jpeg", "jpg"]


def is_allowed(attachment: discord.Attachment):
    """
    Checks if the attachment is allowed

    :param attachment: attachment to check
    :return:
    """
    return attachment.filename.split(".")[-1] in ALLOWED_EXT


class Announcements(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @is_staff()
    @command(
        name="shout",
        description="Make Single Line Announcements on the Channel it was called on"
    )
    @describe(message="The Announcement Message to send")
    async def shout(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str,
    ) -> None:
        """
        Announcement Command that needs a one line message

        :param interactions:
        :param message:
        """
        await interaction.response.send_message(
            f"Announcement has been made",
            ephemeral=True
        )
        await channel.send(message)

    @is_staff()
    @command(
        name="announce",
        description="Make Multiple Line Announcements with Media"
    )
    @describe(photo="The Photo File")
    async def announce(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        photo: Optional[discord.Attachment] = None
    ) -> None:
        """
        Announcement Command that uses modals to make announcements with media

        :param interaction:
        :param photo:
        """

        if photo and not is_allowed(photo):
            return await interaction.response.send_message(
                f"File {photo.filename}, is not a supported file, only send photos with {ALLOWED_EXT}",
                ephemeral=True
            )

        announcement = Announcement(photo, channel)
        await interaction.response.send_modal(announcement)
        await announcement.wait()


async def setup(bot: Bot):
    await bot.add_cog(Announcements(bot))

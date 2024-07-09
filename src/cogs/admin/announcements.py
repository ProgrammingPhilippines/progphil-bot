from typing import Optional

import discord
from discord.ext.commands import Bot, Cog
from discord.app_commands import Choice, choices, command, describe

from src.ui.modals.announcement import Announcement
from src.utils.decorators import is_staff
from src.interface.progphil import IProgPhilBot


ALLOWED_EXT = ["gif", "png", "jpeg", "jpg"]


def is_allowed(attachment: discord.Attachment):
    """
    Checks if the attachment is allowed

    :param attachment: attachment to check
    :return:
    """
    return attachment.filename.split(".")[-1] in ALLOWED_EXT


class Announcements(Cog):
    def __init__(self, bot: IProgPhilBot):
        self.bot = bot

    @is_staff()
    @command(name="shout",
             description="Make Single Line Announcements on the Channel it was called on")
    @describe(channel="Channel to send the announcement to",
              message="The Announcement Message to send")
    async def shout(
        self,
        interaction: discord.Interaction,
        channel: discord.Thread | discord.TextChannel,
        message: str,
    ) -> None:
        """
        Announcement Command that needs a one line message

        :param interaction: Interaction
        :param channel: Channel to send the announcement to
        :param message: Message to send
        """
        await interaction.response.send_message(
            "Announcement has been made",
            ephemeral=True
        )
        await channel.send(message)
        

    @is_staff()
    @command(name="announce",
             description="Make Multiple Line Announcements with Media")
    @choices(
        mention=[Choice(name="yes", value="yes")]
    )
    @choices(
        submission_type=[
            Choice(name="embed", value="embed"),
            Choice(name="regular", value="regular")
        ]
    )
    @describe(channel="Channel to send the announcement to",
              photo="The Photo File")
    async def announce(
        self,
        interaction: discord.Interaction,
        channel: discord.Thread | discord.TextChannel,
        submission_type: Choice[str],
        photo: Optional[discord.Attachment] = None,
        mention: Choice[str] = "",
    ) -> None:
        """
        Announcement Command that uses modals to make announcements with media

        :param interaction: Interacton
        :param channel: The channel to send the announcement to
        :param photo: Photo to send with the announcement
        :param mention: Whether to have mentions or not

        If the command invoker chooses the mention parameter,
        send a selection view that selects roles that they want to mention.

        """

        if photo and not is_allowed(photo):
            return await interaction.response.send_message(
                f"File {photo.filename}, is not a supported file, only send photos with {ALLOWED_EXT}",
                ephemeral=True
            )

        if mention:
            # If the user picked yes
            mention = mention.value

        announcement = Announcement(photo, channel,  submission_type.value, mention)
        await interaction.response.send_modal(announcement)
        await announcement.wait()


async def setup(bot: Bot):
    await bot.add_cog(Announcements(bot))

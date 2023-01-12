import io
import discord
import requests
from discord.ext.commands import Bot, Cog
from discord.app_commands import command, describe, checks
from discord import app_commands

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
        photo_link="The Link to the Photo",
        to_announce="Message to announce"
    )
    @checks.has_any_role(
        *REQUIRED_ROLES
    )
    async def announce_with_media(
            self,
            interaction: discord.Interaction,
            photo_link: str,
            to_announce: str,
    ) -> None:
        """
         Announcement method that needs a link to a photo as an Argument,
         To use the command you must provide a link to the photo you want to send,
         and a single line you want to send
        """
        seperated_photo_link = photo_link.split(".")
        if len(seperated_photo_link) == 0:  # errors when no dots in the given argument
            return await interaction.response.send_message(
                "Provided link is Invalid",
                ephemeral=True
            )
        elif seperated_photo_link[-1] not in ALLOWED_EXT:   # errors when the ext is not allowed
            return await interaction.response.send_message(
                f"Provided link is not allowed, must be a file that ends with {ALLOWED_EXT}",
                ephemeral=True
            )

        request_file = requests.get(photo_link)
        if request_file.status_code != 200:
            return await interaction.response.send_message(
                "Provided link is either not working or Internal Sever Error",
                ephemeral=True
            )

        with io.BytesIO(request_file.content) as file:  # converts to file-like object
            channel = self.bot.get_channel(interaction.channel_id)
            await channel.send(to_announce, file=discord.File(file, f"image_gihapon.{seperated_photo_link[-1]}"))
    @command(
       name="announce",
       description="Make Single Line Announcements on the Channel it was called on"
    ) 
    @describe(message="The Announcement Message to send")
    @checks.has_any_role(
        *REQUIRED_ROLES
    )
    async def announce(self, interactions: discord.Interaction, message: str):
        channel = interactions.channel # get the channel the command was called on
        await interactions.response.send_message(f"Announcement has been made", ephemeral=True) 
        await channel.send(message)

async def setup(bot: Bot):
    await bot.add_cog(Announcements(bot))
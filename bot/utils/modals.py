from discord import Interaction, TextStyle, Attachment
from discord.ui import Modal, TextInput


class Announcement(Modal, title='Announcement'):
    announcement_title = TextInput(
        label='Title',
        placeholder='Title',
        required=True,
    )
    announcement = TextInput(
        label='Announcement',
        placeholder='Announcement',
        required=True,
        style=TextStyle.paragraph
    )

    def __init__(self, attachment: Attachment):
        super().__init__()
        self.attachment = attachment

    async def on_submit(self, interaction: Interaction) -> None:
        channel = interaction.channel
        photo = None

        if self.attachment:  # If the user has uploaded an attachment
            photo = await self.attachment.to_file()

        announcement = format_announcement(self.announcement_title.value, self.announcement.value)  # Formats the announcement
        await channel.send(announcement, file=photo)
        await interaction.response.send_message(
            'Announcement has been sent', ephemeral=True
        )


def format_announcement(title, body):
    """
    Formats the announcement

    :param title: Announcement Title
    :param body: Announcement body
    :return: Formatted announcement
    """

    # This may be modified in future
    return f'**{title}**\n\n{body}'

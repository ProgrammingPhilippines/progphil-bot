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

        if photo := self.attachment:
            photo = await photo.to_file()

        await channel.send(self.announcement_title.value, file=photo)
        await channel.send(self.announcement.value)
        await interaction.response.send_message(
            'Announcement has been sent', ephemeral=True
        )

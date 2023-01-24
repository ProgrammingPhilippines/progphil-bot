from discord import Interaction, TextStyle, Attachment, TextChannel
from discord.ui import Modal, TextInput

from ui.views import AnnouncementView


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

    def __init__(
            self,
            attachment: Attachment,
            channel: TextChannel,
            mention: str = None
            ):
        super().__init__()
        self.attachment = attachment
        self.channel = channel
        self.mention = mention

    async def on_submit(self, interaction: Interaction) -> None:
        photo = None

        if self.attachment:  # If the user has uploaded an attachment
            photo = await self.attachment.to_file()

        announcement = f'**{self.announcement_title.value}**\n\n{self.announcement.value}'

        if self.mention:
            selection_view = AnnouncementView()
            await interaction.response.send_message(view=selection_view, ephemeral=True)
            await selection_view.wait()
            # Gather the "mention" strings of the selected objects
            tags = ("$user", "$role", "$channel")
            user_mentions = [user.mention for user in selection_view.user_mentions]
            role_mentions = [role.mention for role in selection_view.role_mentions]
            channel_mentions = [channel.mention for channel in selection_view.channel_mentions]

            # Format the announcement one by one
            for tag, mention_type in zip(tags, (user_mentions, role_mentions, channel_mentions)):
                if len(mention_type) > 0:  # If the list is empty (any of the following mention lists)
                    announcement = announcement.replace(tag, "{}", len(mention_type))
                    announcement = announcement.format(*mention_type)

        await self.channel.send(announcement, file=photo)

        if interaction.response.is_done():  # if the interaction has been responded to before
            await interaction.followup.send("Announcement sent.", ephemeral=True)
        else:
            await interaction.response.send_message("Announcement sent.", ephemeral=True)

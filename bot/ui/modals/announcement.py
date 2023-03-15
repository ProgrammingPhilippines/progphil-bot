from discord import (
    Embed,
    TextChannel,
    Interaction,
    TextStyle,
    Attachment,
)
from discord.ui import Modal, TextInput

from ui.views.announcement import AnnouncementView


def _unique(iterable: list) -> list:
    """Returns a list with unique items.

    A set wouldn't work since it's unordered.

    :param iterable: The list to remove dupes from.
    """
    r = []

    for item in iterable:
        if item not in r:
            r.append(item)

    return r


class Announcement(Modal, title='Announcement'):
    announcement_title = TextInput(
        label='Title',
        placeholder='Title',
        required=False,
    )
    announcement = TextInput(
        label='Supported Tags: $user, $channel, $role',
        placeholder='Announcement',
        required=True,
        style=TextStyle.paragraph
    )

    def __init__(
            self,
            attachment: Attachment,
            channel: TextChannel,
            submission_type: str,
            mention: str = None
            ):
        self.attachment = attachment
        self.channel = channel
        self.submission_type = submission_type
        self.mention = mention
        super().__init__()

    async def on_submit(self, interaction: Interaction) -> None:
        photo = None
        announcement_title = ""

        if self.attachment:  # If the user has uploaded an attachment
            photo = await self.attachment.to_file()

        if self.announcement_title.value:
            announcement_title = f"**{self.announcement_title.value}**"

        announcement = announcement_title + f'\n\n{self.announcement.value}'

        if self.mention:
            selection_view = AnnouncementView()
            await interaction.response.send_message(view=selection_view, ephemeral=True)
            await selection_view.wait()
            # Gather the "mention" strings of the selected objects
            tags = ("$user", "$role", "$channel")
            user_mentions = [user.mention for user in selection_view.user_mentions]
            role_mentions = [role.mention for role in selection_view.role_mentions]
            channel_mentions = [channel.mention for channel in selection_view.channel_mentions]
            all_mentions = (user_mentions, role_mentions, channel_mentions)

            for tag, mention_type in zip(tags, all_mentions):
                if len(mention_type) < 1:  # If the list is empty (any of the following mention lists)
                    break

                for mention in _unique(mention_type):
                    # Replace the tags one by one
                    announcement = announcement.replace(tag, mention, 1)

        kwargs = (
            {"embed": Embed(description=announcement)},
            {"content": announcement}
        )
        # Hehe i may have made this hard to read
        # Sets the keyword argument based on the condition
        # Very beginner friendly :D
        # Same as this:
        #
        # if self.submission_type == "regular":
        #    await self.channel.send(content=announcement)
        # else:
        #     await self.channel.send(embed=embed)
        await self.channel.send(**kwargs[self.submission_type == "regular"], file=photo)

        if interaction.response.is_done():  # if the interaction has been responded to before
            await interaction.followup.send("Announcement sent.", ephemeral=True)
        else:
            await interaction.response.send_message("Announcement sent.", ephemeral=True)

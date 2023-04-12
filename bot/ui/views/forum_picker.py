from discord import Interaction, ChannelType, ForumChannel
from discord.ui import View, ChannelSelect, select


class ForumPicker(View):
    def __init__(self):
        self.forums: list[ForumChannel] = []
        super().__init__()

    @select(cls=ChannelSelect, channel_types=[ChannelType.forum], max_values=25)
    async def forum_select(self, interaction: Interaction, forum: ChannelSelect):
        self.forums.extend(forum.values)
        await interaction.response.edit_message(content="Success.", view=None)
        self.stop()

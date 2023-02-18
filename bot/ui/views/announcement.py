from discord import (
    Button,
    Interaction,
    Member,
    Role,
    TextChannel,
    ChannelType
)
from discord.ui import (
    View,
    UserSelect,
    RoleSelect,
    ChannelSelect,
    select,
    button
)


class AnnouncementView(View):
    """The view for announcement.

    This view includes UserSelect, RoleSelect and Channel Select.
    Once the view has been submitted, the class variables
    will be loaded with the selected values
    """
    user_mentions: list[Member] = []
    role_mentions: list[Role] = []
    channel_mentions: list[TextChannel] = []

    @select(cls=UserSelect, placeholder="Select users to mention", max_values=25)
    async def user_select(self, interaction: Interaction, selected: UserSelect):
        self.user_mentions.extend(selected.values)
        await interaction.response.send_message("`Selection saved`", ephemeral=True)

    @select(cls=RoleSelect, placeholder="Select roles to mention", max_values=25)
    async def role_select(self, interaction: Interaction, selected: RoleSelect):
        self.role_mentions.extend(selected.values)
        await interaction.response.send_message("`Selection saved`", ephemeral=True)

    @select(
        cls=ChannelSelect, placeholder="Select channels to mention", max_values=25,
        channel_types=[
            ChannelType.text,
            ChannelType.public_thread,
            ChannelType.private_thread,
            ChannelType.forum,
            ChannelType.voice
        ]
    )  # Apparently the categories are breaking the bot.
    async def channel_select(self, interaction: Interaction, selected: ChannelSelect):
        self.channel_mentions.extend(selected.values)
        await interaction.response.send_message("`Selection saved`", ephemeral=True)

    @button(label="Done", emoji="✅")
    async def done_callback(self, interaction: Interaction, button: Button):
        message = (
            f"{len(self.user_mentions)} user(s) selected.\n"
            f"{len(self.channel_mentions)} channel(s) selected.\n"
            f"{len(self.role_mentions)} role(s) selected.\n"
            "Sending announcement..."
        )
        await interaction.response.edit_message(content=message, view=None)
        self.stop()

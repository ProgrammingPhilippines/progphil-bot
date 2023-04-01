from discord import Interaction, User, Role, ButtonStyle, ChannelType
from discord.ui import (
    Button,
    View,
    UserSelect,
    RoleSelect,
    ChannelSelect,
    button,
    select
)


class TaggingSelection(View):
    def __init__(self):
        self.selected: list[User | Role] = []
        self.forum: int = None
        super().__init__()

    @select(cls=UserSelect, placeholder="Select users...", max_values=25)
    async def select_users(self, interaction: Interaction, selection: UserSelect):
        self.selected.extend(selection.values)

        await interaction.response.send_message(
            f"Selected {len(selection.values)} user(s).",
            ephemeral=True
        )

    @select(cls=RoleSelect, placeholder="Select roles...", max_values=25)
    async def select_roles(self, interaction: Interaction, selection: RoleSelect):
        self.selected.extend(selection.values)

        await interaction.response.send_message(
            f"Selected {len(selection.values)} role(s).",
            ephemeral=True
        )

    @select(
        cls=ChannelSelect,
        placeholder="Select forum...",
        channel_types=[ChannelType.forum],
        min_values=1,
        max_values=1
    )
    async def select_forum(self, interaction: Interaction, selection: RoleSelect):
        self.forum = selection.values[0].id

        await interaction.response.send_message(
            f"Selected {selection.values[0].name}",
            ephemeral=True
        )

    @button(label="Submit", style=ButtonStyle.green)
    async def submit(self, interaction: Interaction, button: Button):
        if not self.forum:
            await interaction.response.send_message(
                "Please select a forum.",
                ephemeral=True
            )
            return

        await interaction.response.edit_message(content="Done!")
        self.stop()

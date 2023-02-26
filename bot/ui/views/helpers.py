from discord import Interaction, User, Role, ButtonStyle
from discord.ui import (
    Button,
    View,
    UserSelect,
    RoleSelect,
    button,
    select
)


class HelperSelection(View):
    def __init__(self):
        self.selected: list[User | Role] = []
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

    @button(label="Submit", style=ButtonStyle.green)
    async def submit(self, interaction: Interaction, button: Button):
        await interaction.response.edit_message(content="Selection complete.", view=None)
        self.stop()

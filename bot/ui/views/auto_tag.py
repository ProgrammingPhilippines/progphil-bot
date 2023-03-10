from discord import Interaction, User, Role, ButtonStyle, ChannelType
from discord.ui import (
    Button,
    View,
    Modal,
    TextInput,
    UserSelect,
    RoleSelect,
    ChannelSelect,
    button,
    select
)


class TaggingSelection(View):
    def __init__(self):
        self.selected: list[User | Role] = []
        self.forum: int
        self.message: str
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

    @select(cls=ChannelSelect, placeholder="Select forum...", channel_types=[ChannelType.forum], min_values=1)
    async def select_forum(self, interaction: Interaction, selection: RoleSelect):
        self.forum = selection.values[0].id

        await interaction.response.send_message(
            f"Selected {selection.values[0].name}",
            ephemeral=True
        )

    @button(label="Submit", style=ButtonStyle.green)
    async def submit(self, interaction: Interaction, button: Button):
        async def callback(interaction: Interaction):
            """The modal's callback so we don't get an error"""
            await interaction.response.send_message("Success.", ephemeral=True)

        modal = Modal(title="Set Custom Message")
        msg = TextInput(
            label="Add custom message.",
            placeholder="Type here... (Leave blank for default message.)",
            default="Calling out peeps!\n\n"
        )
        modal.on_submit = callback
        modal.add_item(msg)
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.message = msg.value

        self.stop()

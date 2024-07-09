from discord import (
    Interaction,
    User,
    Role,
    ButtonStyle,
    ChannelType
)
from discord.ui import (
    Button,
    Modal,
    View,
    UserSelect,
    RoleSelect,
    ChannelSelect,
    TextInput,
    button,
    select
)

from src.data.forum.auto_tag import AutoTagDB


class TaggingSelection(View):
    def __init__(self, db: AutoTagDB):
        self.db = db
        self.selected: User | Role | None = None
        self.forum: int | None = None
        self.custom_msg: str = "Calling out peeps!"
        super().__init__()

    async def _inadequate_check(self, interaction: Interaction):
        if not self.forum:
            await interaction.response.send_message(
                "Please select a forum.",
                ephemeral=True
            )
            return False

        if not self.selected:
            await interaction.response.send_message(
                "Please select users/roles.",
                ephemeral=True
            )
            return False

        return True

    @select(cls=UserSelect, placeholder="Select users...")
    async def select_user(self, interaction: Interaction, selection: UserSelect):
        self.selected = selection.values[0]

        await interaction.response.edit_message(
            content=f"Selected {self.selected.mention}",
            view=self.remove_item(self.select_role)
        )

    @select(cls=RoleSelect, placeholder="Select roles...")
    async def select_role(self, interaction: Interaction, selection: RoleSelect):
        self.selected = selection.values[0]

        await interaction.response.edit_message(
            content=f"Selected {self.selected.mention}",
            view=self.remove_item(self.select_user)
        )

    @select(
        cls=ChannelSelect,
        placeholder="Select forum...",
        channel_types=[ChannelType.forum]
    )
    async def select_forum(self, interaction: Interaction, selection: RoleSelect):
        self.forum = selection.values[0].id

        await interaction.response.send_message(
            f"Selected {selection.values[0].name}",
            ephemeral=True
        )

    @button(label="Submit", style=ButtonStyle.green)
    async def submit(self, interaction: Interaction, button: Button):
        if not await self._inadequate_check(interaction):
            return

        async def callback(interaction: Interaction):
            """The modal's callback so we don't get an error"""

            self.custom_msg = msg.value
            await interaction.response.edit_message(
                content="Success.",
                view=None
            )

        modal = Modal(title="Set Custom Message")
        msg = TextInput(
            label="Add custom message.",
            placeholder="Type here...",
            default=self.custom_msg
        )
        modal.on_submit = callback
        modal.add_item(msg)
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.stop()

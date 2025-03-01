from discord.ui import View, button
from discord import Message, Thread, ButtonStyle, Interaction, Button


class MarkAsSolution(View):
    def __init__(self, thread: Thread, message: Message):
        super().__init__(timeout=None)
        self.thread = thread
        self.message = message
        self.confirmed = False

    @button(label="Yes", style=ButtonStyle.green)  # type: ignore
    async def accept(self, interaction: Interaction, button: Button):
        self.confirmed = True
        self.stop()

    @button(label="No", style=ButtonStyle.red)  # type: ignore
    async def decline(self, interaction: Interaction, button: Button):
        self.confirmed = False
        await interaction.response.send_message("Cancelled.", ephemeral=True)
        self.stop()

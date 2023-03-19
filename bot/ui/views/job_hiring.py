from discord import Interaction, ButtonStyle
from discord.ui import View, Button, button

from ui.modals.job_hiring import OncePerDay, SpecificDate, Recurring


class JobConfig(View):
    choice: int
    sched: str

    def __init__(self):
        super().__init__()

    @button(label="1", style=ButtonStyle.primary)
    async def button1(self, interaction: Interaction, button: Button):
        modal = OncePerDay()

        await interaction.response.send_modal(modal)
        await modal.wait()

        self.choice = 1
        self.sched = modal.sched
        self.stop()

    @button(label="2", style=ButtonStyle.primary)
    async def button2(self, interaction: Interaction, button: Button):
        modal = SpecificDate()

        await interaction.response.send_modal(modal)
        await modal.wait()

        self.choice = 2
        self.sched = modal.sched
        self.stop()

    @button(label="3", style=ButtonStyle.primary)
    async def button3(self, interaction: Interaction, button: Button):
        modal = Recurring()

        await interaction.response.send_modal(modal)
        await modal.wait()

        self.choice = 3
        self.sched = modal.sched
        self.stop()

    async def on_timeout(self) -> None:
        """Gets called when the view expires."""

        self.choice = 0
        self.sched = ""

    # TODO: Make a regex validator on modal instance variable after submitting.
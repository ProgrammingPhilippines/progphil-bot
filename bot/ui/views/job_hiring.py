from asyncpg import Pool
from discord import Interaction, ButtonStyle, TextChannel
from discord.ui import View, Button, button

from ui.modals.job_hiring import OncePerDay, SpecificDate, Recurring
from database.job_hiring import JobHiringDB


class JobConfig(View):

    def __init__(self, pool: Pool, channel: TextChannel, sched_type: str):
        self.type = sched_type
        self.channel = channel
        self.db = JobHiringDB(pool)
        super().__init__()

    @button(label="1", style=ButtonStyle.primary)
    async def button1(self, interaction: Interaction, button: Button):
        modal = OncePerDay()

        await interaction.response.send_modal(modal)
        await modal.wait()

        if self.type == "setup":
            await self.db.insert(
                channel_id=self.channel.id,
                schedule=modal.sched,
                schedule_type=modal.schedule_type
            )
        else:
            await self.db.update(
                channel_id=self.channel.id,
                schedule=modal.sched,
                schedule_type=modal.schedule_type
            )

        self.stop()

    @button(label="2", style=ButtonStyle.primary)
    async def button2(self, interaction: Interaction, button: Button):
        modal = SpecificDate()

        await interaction.response.send_modal(modal)
        await modal.wait()

        if self.type == "setup":
            await self.db.insert(
                channel_id=self.channel.id,
                schedule=modal.sched,
                schedule_type=modal.schedule_type
            )
        else:
            await self.db.update(
                channel_id=self.channel.id,
                schedule=modal.sched,
                schedule_type=modal.schedule_type
            )

        self.stop()

    @button(label="3", style=ButtonStyle.primary)
    async def button3(self, interaction: Interaction, button: Button):
        modal = Recurring()

        await interaction.response.send_modal(modal)
        await modal.wait()

        if self.type == "setup":
            await self.db.insert(
                channel_id=self.channel.id,
                schedule=modal.sched,
                schedule_type=modal.schedule_type
            )
        else:
            await self.db.update(
                channel_id=self.channel.id,
                schedule=modal.sched,
                schedule_type=modal.schedule_type
            )

        self.stop()

    async def on_timeout(self) -> None:
        """Gets called when the view expires."""

        del self

    # TODO: Make a regex validator on modal instance variable after submitting.
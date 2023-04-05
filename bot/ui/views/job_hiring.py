from asyncpg import Pool
from discord import Interaction, ButtonStyle, TextChannel
from discord.ui import View, Button, Item, button

from ui.modals.job_hiring import OncePerDay, SpecificDate, Recurring
from database.job_hiring import JobHiringDB
from utils.utils import validate_time, validate_date, parse


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

        if not validate_time(modal.sched):
            raise Exception("Please enter the correct format. HH:MM")

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

        schedule = validate_date(modal.sched)

        if not schedule:
            raise Exception("Please enter a correct format and a valid date. MM/DD/YYYY")

        if self.type == "setup":
            await self.db.insert(
                channel_id=self.channel.id,
                schedule=str(int(schedule)),
                schedule_type=modal.schedule_type
            )
        else:
            await self.db.update(
                channel_id=self.channel.id,
                schedule=str(int(schedule)),
                schedule_type=modal.schedule_type
            )

        self.stop()

    @button(label="3", style=ButtonStyle.primary)
    async def button3(self, interaction: Interaction, button: Button):
        modal = Recurring()

        await interaction.response.send_modal(modal)
        await modal.wait()

        if not parse(modal.sched):
            raise Exception("Enter a valid schedule.")

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

    async def on_error(self, interaction: Interaction, error: Exception, item: Item) -> None:
        await interaction.followup.send(
            content=error,
            ephemeral=True
        )

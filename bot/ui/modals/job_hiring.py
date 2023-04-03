from discord import Interaction, TextStyle
from discord.ui import Modal, TextInput


class OncePerDay(Modal):
    schedule_type = 0
    title = "Every Day At A Specific Time."
    sched = TextInput(
        label="Input the desired time.",
        placeholder="Enter time in HH:MM format.",
        style=TextStyle.short
    )

    async def on_submit(self, interaction: Interaction) -> None:
        self.sched = self.sched.value
        await interaction.response.send_message("Submitted.", ephemeral=True)


class SpecificDate(OncePerDay):
    schedule_type = 1
    title = "Once On A Specific Day"
    sched = TextInput(
        label="Input the desired date.",
        placeholder="Enter date in MM/DD/YY format.",
        style=TextStyle.short
    )


class Recurring(OncePerDay):
    schedule_type = 2
    title = "Every N [months|days|hours|minutes|seconds]"
    sched = TextInput(
        label="Input the desired schedule.",
        placeholder="Enter schedule... (ex. 1month1day1hour)",
        style=TextStyle.short
    )

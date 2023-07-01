# pylint: disable = no-member

import asyncio
from enum import IntEnum

from discord import Embed, Interaction, Role, TextStyle, Forbidden
from discord.ui import Modal, TextInput
from discord.app_commands import Choice, choices, command
from discord.utils import utcnow
from discord.ext.commands import Bot, GroupCog
from discord.ext.tasks import loop

from config import GuildInfo
from utils.decorators import is_staff
from database.config_auto import Config
from database.user_reminder import UserReminderDB


class Day(IntEnum):
    MON = 1
    TUE = 2
    WED = 3
    THU = 4
    FRI = 5
    SAT = 6
    SUN = 7


class Frequency(IntEnum):
    PER_MONTH = 1
    PER_WEEK = 2


DAYS = [
    Choice(name=day.name, value=day) for day in Day
]

FREQUENCY = [
    Choice(name="Per Month", value=Frequency.PER_MONTH.value),
    Choice(name="Per Week", value=Frequency.PER_WEEK.value)
]


class UserReminder(GroupCog):
    message: str
    day: int
    interval: int
    member_role: Role
    visitor_role: Role
    current_week: int
    current_month: int

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Config(self.bot.pool)
        self.db = UserReminderDB(self.bot.pool)
        self.week_sent = False
        self.month_sent = False

    async def before_load(self):
        await self.bot.wait_until_ready()
        date = utcnow()

        self.current_month = date.month
        self.current_week = date.isocalendar()[1]

        await self._update()

    async def cog_load(self):
        asyncio.create_task(self.before_load())

    @loop(hours=24)
    async def reminder_loop(self):
        status = await self.config.get_config("user_reminder")

        if not status["config_status"]:
            return

        date_now = utcnow()
        week = date_now.isocalendar()[1]
        should_send = False

        if self.current_week != week:
            self.current_week = week
            self.week_sent = False

        if self.current_month != date_now.month:
            self.current_month = date_now.month
            self.month_sent = False

        if self.interval == Frequency.PER_WEEK:
            if self.week_sent:
                return

            if date_now.weekday() + 1 == self.day:
                should_send = True
                self.week_sent = True

        if self.interval == Frequency.PER_MONTH:
            if self.month_sent:
                return

            if date_now.weekday() + 1 == self.day:
                should_send = True
                self.month_sent = True

        if should_send:
            asyncio.create_task(self.check_onboarding())

    async def check_onboarding(self):
        """Checks every member and contacts them if they're not onboarded."""

        guild = self.get_guild()

        for member in guild.members:
            if len(member.roles) > 1:
                continue

            if self.member_role == member.roles[0] or self.visitor_role == member.roles[0]:
                try:
                    await member.send(embed=Embed(description=self.message))
                except Forbidden:
                    pass

    def get_guild(self):
        """Get the guild instance."""

        r_channel = self.bot.get_channel(GuildInfo.dev_help_forum)  # to get the guild from the channel
        return r_channel.guild

    async def _update(self):
        setting = await self.db.get_config()

        if not setting:
            return

        for set in setting:
            if set is None:
                return

        self.message = setting["message"] or "Don't forget to onboard properly!"
        self.day = setting["day"]
        self.interval = setting["interval"]

        guild = self.get_guild()

        self.member_role = guild.get_role(setting["member_role"])
        self.visitor_role = guild.get_role(setting["visitor_role"])

    @is_staff()
    @command(name="toggle", description="Toggle the user reminder")
    async def toggle(self, interaction: Interaction) -> None:
        """
        Toggles the trivia.
        """

        toggle_map = {
            True: "ON",
            False: "OFF"
        }

        config = "user_reminder"

        if not await self.config.get_config(config):
            await self.config.add_config(config)

        toggle = await self.config.toggle_config(config)

        await interaction.response.send_message(
            f"Turned {toggle_map[toggle]} User Reminder.",
            ephemeral=True
        )

    @is_staff()
    @command(name="message", description="Set/Edit the user reminder message")
    async def set_message(self, interaction: Interaction):
        async def modal_cb(interaction: Interaction):
            await self.db.set_config("message", text.value)
            await interaction.response.send_message("Success.", ephemeral=True)

        modal = Modal(title="Custom Reminder Message")
        text = TextInput(
            label="Custom Message",
            style=TextStyle.long,
            max_length=2000
        )

        modal.add_item(text)
        modal.on_submit = modal_cb
        await interaction.response.send_modal(modal)
        await self._update()

    @is_staff()
    @choices(
        day=DAYS,
        interval=FREQUENCY
    )
    @command(name="schedule", description="Setup the user reminder schedule")
    async def sched(self, interaction: Interaction, day: Choice[int], interval: Choice[int]):
        await self.db.set_config("day", day.value)
        await self.db.set_config("interval", interval.value)
        await interaction.response.send_message("Success.", ephemeral=True)
        await self._update()

    @is_staff()
    @command(name="setup", description="Setup the user reminder")
    async def setup(
        self,
        interaction: Interaction,
        member_role: Role,
        visitor_role: Role
    ) -> None:
        """
        Setup the user reminder
        """

        if member_role == visitor_role:
            return await interaction.response.send_message(
                "Both roles can't be the same!",
                ephemeral=True
            )

        await self.db.set_config("member_role", member_role.id)
        await self.db.set_config("visitor_role", visitor_role.id)
        await interaction.response.send_message(
            "User Reminder setup complete.",
            ephemeral=True
        )
        await self._update()


async def setup(bot: Bot):
    await bot.add_cog(UserReminder(bot))

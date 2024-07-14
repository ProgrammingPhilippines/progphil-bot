# pylint: disable = no-member

import asyncio

from asyncpg import Record
from discord import Embed, Interaction, ForumChannel, TextStyle
from discord.app_commands import Choice, command, choices
from discord.ext import tasks
from discord.ui import Modal, TextInput, View, Select
from discord.utils import utcnow
from discord.ext.commands import Bot, GroupCog

from src.data.admin.config_auto import Config
from src.data.forum.forum_cleanup import ForumCleanupDB
from src.utils.decorators import is_staff
from src.ui.views.forum_picker import ForumPicker


DAY_HR = 24
WEEK_HR = DAY_HR * 7

sched_mapping = {
    "day": DAY_HR,
    "week": WEEK_HR
}


class ForumCleanup(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = ForumCleanupDB(self.bot.pool)
        self.toggle_config = Config(self.bot.pool)
        self.forums: list[ForumChannel] | None = None
        self.conf: list[Record] | None = None

    async def _archive_threads(self, forum: ForumChannel, conf: list[Record]):
        """Archives a thread.

        :param forum: The forum to check
        :param conf: The configurations
        """

        close_t, = conf
        now = utcnow()
        c_message = await self.db.get_message("close")

        if not c_message:
            c_message = "Archived due to inactivity."
        else:
            c_message = c_message[0]["c_message"]

        embed = Embed(description=c_message)

        for thread in forum.threads:
            message, = [m async for m in thread.history(limit=1)]
            days_inactive = (now - message.created_at).days

            if days_inactive >= close_t["num_days"] and not thread.flags.pinned:
                await thread.send(embed=embed)
                await thread.edit(archived=True, reason="Inactivity")

    async def _refresh_task(self):
        if self.thread_check.is_running():
            self.thread_check.restart()
        else:
            self.thread_check.start()

    async def _refresh_requirements(self):
        await self.bot.wait_until_ready()
        forums = await self.db.get_forums()
        forum_ids = [f["forum_id"] for f in forums]
        self.forums = list(map(self.bot.get_channel, forum_ids))
        self.conf = await self.db.get_conf()

    async def cog_load(self):
        asyncio.create_task(self._refresh_requirements())
        sched = await self.db.get_schedule()

        if not sched:
            return

        sched, = sched

        self.thread_check.change_interval(hours=sched_mapping[sched["duration_unit"]])
        self.thread_check.start()

    @tasks.loop()
    async def thread_check(self):
        config = await self.toggle_config.get_config("forum_cleanup")

        if not config["config_status"]:
            return

        if not self.forums:
            return

        if not self.conf:
            return

        for forum in self.forums:
            await self._archive_threads(forum, self.conf)

    @is_staff()
    @choices(
        choice=[
            Choice(name="Add", value="add"),
            Choice(name="Remove", value="remove"),
            Choice(name="View all", value="view")
        ]
    )
    @command(name="forums", description="Manages forums")
    async def manage_forums(self, interaction: Interaction, choice: Choice[str]):
        if choice.value == "add":
            view = ForumPicker()
            await interaction.response.send_message(
                "Select Forums to add.",
                view=view,
                ephemeral=True
            )
            await view.wait()
            await self.db.add_forums([f.id for f in view.forums])
        elif choice.value == "remove":
            async def select_callback(interaction: Interaction):
                await interaction.response.edit_message(content="Success...", view=None)
                view.stop()

            forums = await self.db.get_forums()

            view = View()
            select = Select(max_values=len(forums))
            select.callback = select_callback

            for forum in forums:
                forum = interaction.guild.get_channel(
                    forum["forum_id"]
                )

                if not forum:
                    continue

                select.add_option(
                    label=forum.name,
                    value=forum.id
                )

            view.add_item(select)
            await interaction.response.send_message(
                "Select channels to remove",
                view=view,
                ephemeral=True
            )
            await view.wait()
            await self.db.remove_forums(map(int, select.values))
        else:
            embed = Embed(
                title=f"All Forums allowed for ForumCleanup"
            )

            desc = ""
            forums = await self.db.get_forums()
            n = 1

            for forum in forums:
                forum = interaction.guild.get_channel(
                    forum["forum_id"]
                )

                if not forum:
                    continue

                desc += f"{n}. {forum.mention}\n"
                n += 1

            embed.description = desc or "Nothing yet..."
            await interaction.response.send_message(embed=embed, ephemeral=True)

        await self._refresh_requirements()

    @is_staff()
    @choices(
        every=[
            Choice(name="day", value="day"),
            Choice(name="week", value="week")
        ]
    )
    @command(name="schedule", description="Schedule the forum cleanup once every [ ? ]")
    async def schedule(self, interaction: Interaction, every: Choice[str]):
        """Sets the schedule for the bot"""

        sched = every.value
        hrs = sched_mapping[sched]

        await self.db.upsert_schedule(sched)
        self.thread_check.change_interval(hours=hrs)
        await self._refresh_task()
        await interaction.response.send_message(
            "Success.",
            ephemeral=True
        )

    @command(name="config", description="Schedule the forum cleanup")
    async def cleanup_conf(self, interaction: Interaction):
        """Setup/Update the config"""

        async def modal_callback(interaction: Interaction):
            close_value = close.value

            if not close_value.isdecimal():
                return await interaction.response.send_message(
                    "Please enter valid digits.",
                    ephemeral=True
                )

            await self.db.upsert_conf("close", int(close_value))
            await self.db.upsert_message("close", c_message.value)
            await self._refresh_requirements()
            await interaction.response.send_message(
                "Success.",
                ephemeral=True
            )

        modal = Modal(title=f"{self.__cog_name__} Configurations")
        close = TextInput(label="Days inactive before closing a thread")
        c_message = TextInput(
            label="Message to send after closing a thread",
            style=TextStyle.long
        )

        modal.add_item(close)
        modal.add_item(c_message)
        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    @is_staff()
    @command(name="toggle", description="Toggles this feature")
    async def toggle(self, interaction: Interaction):
        """Toggles Forum Cleanup"""

        toggle_map = {
            True: "ON",
            False: "OFF"
        }

        toggle = await self.toggle_config.toggle_config("forum_cleanup")

        await interaction.response.send_message(
            f"Turned {toggle_map[toggle]} {self.qualified_name}.",
            ephemeral=True
        )


async def setup(bot: Bot):
    await bot.add_cog(ForumCleanup(bot))

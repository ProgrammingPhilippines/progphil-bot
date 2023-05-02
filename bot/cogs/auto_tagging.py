from discord import (
    Embed,
    Forbidden,
    Guild,
    HTTPException,
    Interaction,
    PartialMessage,
    Thread,
    Member,
    Role
)
from discord.app_commands import command, describe
from discord.ext.commands import Bot, Cog, GroupCog

from database.auto_tag import AutoTagDB
from database.config_auto import Config
from utils.decorators import is_staff
from ui.views.auto_tag import TaggingSelection


def _getter(guild: Guild, entry: dict) -> Member | Role:
    """Gets the object type and returns it."""

    if entry["obj_type"] == "role":
        getter = guild.get_role
    else:
        getter = guild.get_member

    return getter(entry["obj_id"])


class Tagging(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = AutoTagDB(self.bot.pool)
        self.config = Config(self.bot.pool)

    async def attempt_send(
        self,
        thread: Thread,
        thread_msg: PartialMessage,
        message: str,
        attempt: int = 0
    ):
        """Attempts to send a message to the thread.

        Will retry everytime it fails until 5 tries.

        :param thread: The thread to send to
        :param thread_msg: The thread message
        :param message: The message to send
        :param attempt: Starting attempt number"""

        if attempt > 5:
            return

        try:
            await thread_msg.pin()
            await thread.send(message)
        except (HTTPException, Forbidden):
            await self.attempt_send(thread, thread_msg, message, attempt + 1)

    @Cog.listener()
    async def on_thread_create(self, thread: Thread):
        config = await self.config.get_config("auto_tagging")

        if not config["config_status"]:
            return

        entry = await self.db.get_entry(thread.parent.id)

        if not entry:
            return

        message = f"{_getter(thread.guild, entry).mention}\n{entry['c_message']}\n\n"

        thread_msg = thread.get_partial_message(thread.id)

        await self.attempt_send(thread, thread_msg, message)

    @is_staff()
    @command(name="toggle", description="Toggles the auto tagging.")
    async def toggle_config(self, interaction: Interaction):
        """Toggles auto tagging."""

        toggle_map = {
            True: "ON",
            False: "OFF"
        }

        toggle = await self.config.toggle_config("auto_tagging")

        await interaction.response.send_message(
            f"Turned {toggle_map[toggle]} Auto Tagging.",
            ephemeral=True
        )

    @is_staff()
    @command(name="manage", description="Add/Edit an auto tag.")
    async def manage_entries(self, interaction: Interaction):
        """Adds an entry to the database."""

        view = TaggingSelection(self.db)
        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()

        entry = view.selected

        if not view.selected:
            return

        if isinstance(entry, Member):
            obj_type = "user"
        elif isinstance(entry, Role):
            obj_type = "role"

        await self.db.upsert_entry(entry.id, obj_type, view.forum, view.custom_msg)

    @is_staff()
    @command(name="remove", description="Removes an auto tag.")
    @describe(entry_id="The entry's ID. (do /tagging view to check their corresponding IDs.)")
    async def remove_entry(self, interaction: Interaction, entry_id: int):
        """Removes an entry from the database.

        :param entry_id: The entry's ID from the database. (not the obj_id.)"""

        if await self.db.remove_entry(entry_id):
            message = f"Successfully removed entry with ID: {entry_id}"
        else:
            message = f"Auto Tag with ID: {entry_id} may not exist."

        await interaction.response.send_message(
            message,
            ephemeral=True
        )

    @is_staff()
    @command(name="all", description="Views all auto tags.")
    async def view_auto_tags(self, interaction: Interaction):
        """Views all PPH entries."""

        entry = await self.db.view_entries()
        embed = Embed(description="**All PPH Auto Tags.**\n\n")

        if not entry:
            embed.description += "None yet..."

        for entry in entry:
            # Use the defined getted to get the entry type.
            obj = _getter(interaction.guild, entry)
            forum = interaction.guild.get_channel(entry['forum_id'])
            embed.description += (
                f"`ID:` {entry['id']} - {obj.mention}\n"
                f"`Forum:` {forum.mention if forum else 'Not Found'}\n"
                f"`Type:` {entry['obj_type'].title()}\n"
                f"`Message`: {entry['c_message']}\n\n"
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot: Bot):
    await bot.add_cog(Tagging(bot))

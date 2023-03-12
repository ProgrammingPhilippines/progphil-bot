from discord import (
    Embed,
    Guild,
    HTTPException,
    Interaction,
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

    @Cog.listener()
    async def on_thread_create(self, thread: Thread):
        config = await self.config.get_config("auto_tagging")

        if not config["config_status"]:
            return

        entries = await self.db.view_from_forum(thread.parent.id)

        if not entries:
            return

        # Get all the forum ID's of the entries
        forum_ids = [f["tag_in"] for f in map(dict, entries)]

        if thread.parent_id not in forum_ids:
            return

        to_mention = []
        message = ""

        for entry in map(dict, entries):
            # Here just check if the thread parent (forum)
            # matches any of the entries
            if entry["tag_in"] == thread.parent.id:
                message = entry["msg"] + "\n\n"
                to_mention.append(_getter(thread.guild, entry).mention)

        # Add the mentions to the message
        message += "\n".join(to_mention)
        thread_msg = thread.get_partial_message(thread.id)

        try:
            await thread_msg.pin()
        except HTTPException:
            pass

        await thread.send(message)

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
    @command(name="add", description="Adds an auto tag.")
    async def add_entries(self, interaction: Interaction):
        """Adds an entry to the database."""

        view = TaggingSelection()
        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()

        for entry in view.selected:
            # Set the entry's obj_type based on their instance
            if isinstance(entry, Member):
                obj_type = "user"
            elif isinstance(entry, Role):
                obj_type = "role"

            await self.db.add_entry(entry.id, obj_type, view.forum, view.message)

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

        for entry in map(dict, entry):
            # Convert the `asyncpg.Record` objects to dicts
            # for better formatting.

            # Use the defined getted to get the entry type.
            obj = _getter(interaction.guild, entry)
            forum = interaction.guild.get_channel(entry['tag_in'])
            embed.description += (
                f"ID: {entry['id']} - {obj.mention}\n"
                f"Forum: {forum.mention if forum else 'Not Found'}\n"
                f"Type: {entry['obj_type'].title()}\n\n"
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot: Bot):
    await bot.add_cog(Tagging(bot))

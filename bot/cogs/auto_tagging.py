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

from config import GuildInfo
from database.helpers import HelpersDB
from utils.decorators import is_staff
from ui.views.helpers import HelperSelection


def _getter(guild: Guild, helper: dict) -> Member | Role:
    """Gets the object type and returns it."""

    if helper["obj_type"] == "role":
        getter = guild.get_role
    else:
        getter = guild.get_member

    return getter(helper["obj_id"])


class Helpers(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = HelpersDB(self.bot.pool)

    @Cog.listener()
    async def on_thread_create(self, thread: Thread):
        if thread.parent_id != GuildInfo.dev_help_forum:
            return

        thread_msg = thread.get_partial_message(thread.id)

        try:
            await thread_msg.pin()
        except HTTPException:
            pass

        message = "Calling out helpers!\n"
        helpers = await self.db.view_helpers()

        for helper in map(dict, helpers):
            helper = _getter(thread.guild, helper)

            if helper:
                message += helper.mention + "\n"

        await thread.send(message)

    @is_staff()
    @command(name="add", description="Adds a PPH helper.")
    async def add_helpers(self, interaction: Interaction):
        """Adds a helper to the database."""

        view = HelperSelection()
        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()

        for helper in view.selected:
            # Set the helper's obj_type based on their instance
            if isinstance(helper, Member):
                obj_type = "user"
            elif isinstance(helper, Role):
                obj_type = "role"

            await self.db.add_helper(helper.id, obj_type)

    @is_staff()
    @command(name="remove", description="Removes a PPH helper.")
    @describe(helper_id="The helper's ID. (do /helpers view to check their corresponding IDs.)")
    async def remove_helper(self, interaction: Interaction, helper_id: int):
        """Removes a helper from the database.

        
        :param helper_id: The helper's ID from the database. (not the obj_id.)"""

        if await self.db.remove_helper(helper_id):
            message = f"Successfully removed helper with ID: {helper_id}"
        else:
            message = f"Helper with ID: {helper_id} may not exist."

        await interaction.response.send_message(
            message,
            ephemeral=True
        )

    @is_staff()
    @command(name="all", description="Views all PPH helpers.")
    async def view_helpers(self, interaction: Interaction):
        """Views all PPH helpers."""

        helpers = await self.db.view_helpers()
        embed = Embed(description="**All PPH Helpers.**\n\n")

        if not helpers:
            embed.description += "None yet..."

        for helper in map(dict, helpers):
            # Convert the `asyncpg.Record` objects to dicts
            # for better formatting.

            # Use the defined getted to get the helper type.
            obj = _getter(interaction.guild, helper)

            embed.description += (
                f"ID: {helper['id']} - {obj.mention}\n"
                f"Type: {helper['obj_type'].title()}\n\n"
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot: Bot):
    await bot.add_cog(Helpers(bot))

from discord import (
    Forbidden,
    Guild,
    HTTPException,
    Interaction,
    Thread,
    Member,
    Role
)
from discord.app_commands import command, describe
from discord.ext.commands import Bot, Cog, GroupCog

from database.post_assist import PostAssistDB
from database.config_auto import Config
from utils.decorators import is_staff
from ui.views.post_assist import (
    ConfigurePostAssist,
    ConfigurationPagination,
    format_data,
)


def _getter(guild: Guild, entry: dict) -> Member | Role:
    """Gets the object type and returns it."""

    if entry["entity_type"] == "role":
        getter = guild.get_role
    else:
        getter = guild.get_member

    return getter(entry["entity_id"])


class ForumAssist(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = PostAssistDB(self.bot.pool)
        self.config = Config(self.bot.pool)

    @Cog.listener()
    async def on_thread_create(self, thread: Thread):
        config = await self.config.get_config("auto_tagging")

        if not config["config_status"]:
            return

        entry = await self.db.config_by_forum(thread.parent.id)

        if not entry:
            return

        reply = await self.db.get_reply(entry["id"])
        tags = await self.db.get_tags(entry["id"])
        tag_message = await self.db.get_tag_message(entry["id"])

        thread_msg = thread.get_partial_message(thread.id)

        # Sometimes the pinning and reply fails 
        # when the thread is created and the bot 
        # tries to reply before the author's first message gets sent.
        # So we try at a maximum of 5 times to pin and reply.
        for _ in range(5):
            try:
                await thread_msg.pin()

                if reply:
                    await thread.send(reply)

                break
            except (Forbidden, HTTPException):
                pass

        if tags and tag_message:
            message = ""

            for tag in tags:
                message += f"{_getter(thread.guild, tag).mention}\n"

            message += tag_message

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
    @command(name="new", description="Add a new configuration.")
    async def create_new(self, interaction: Interaction):
        """Adds an entry to the database."""

        await interaction.response.defer(ephemeral=True)

        view = ConfigurePostAssist()
        await interaction.followup.send(
            "Configure Post Assist",
            view=view,
            ephemeral=True
        )
        await view.wait()

        forum = view.forum
        reply = view.custom_msg
        tags = view.tag_list
        tag_message = view.tag_message

        if await self.db.config_by_forum(forum):
            return await interaction.followup.send(
                "There is already a configuration for this forum.",
                ephemeral=True
            )

        if not (view.tag_list or view.custom_msg):
            return await interaction.followup.send(
                "You must provide either tags or a custom message.",
                ephemeral=True
            )

        if view.finished:
            await interaction.followup.send("Success!", ephemeral=True)
            await self.db.add_configuration(
                forum_id=forum,
                entities=tags,
                entity_tag_message=tag_message,
                reply=reply
            )
            return

        await interaction.followup.send("Cancelled.", ephemeral=True)

    @is_staff()
    @command(name="delete", description="Deletes a configuration.")
    @describe(config_id="The configuration ID")
    async def delete(self, interaction: Interaction, config_id: int):
        """Removes an entry from the database.

        :param config_id: The configuration ID from the database.
        """

        if await self.db.get_config(config_id):
            message = f"Successfully removed entry with ID: {config_id}"
            await self.db.delete_configuration(config_id)
        else:
            message = f"Configuration ID: {config_id} may not exist."

        await interaction.response.send_message(
            message,
            ephemeral=True
        )

    @is_staff()
    @command(name="list", description="Views all configurations.")
    async def view_all(self, interaction: Interaction):
        """Views all PPH entries."""

        result = await self.db.list_configurations()

        if not result:
            return await interaction.response.send_message(
                "There are no configurations.",
                ephemeral=True
            )

        view = ConfigurationPagination(result, _getter)
        view.previous.disabled = True

        if not result[1:]:
            view.next.disabled = True

        await interaction.response.send_message(
            format_data(result[0], interaction.guild, _getter),
            view=view,
        )
        await view.wait()

    @is_staff()
    @command(name="edit", description="Edits a configuration.")
    @describe(config_id="The configuration ID")
    async def edit(self, interaction: Interaction, config_id: int):
        """Edits an entry from the database.

        :param config_id: The configuration ID from the database.
        """

        config = await self.db.get_config(config_id)

        if not config:
            return await interaction.response.send_message(
                f"Configuration ID: {config_id} may not exist.",
                ephemeral=True
            )

        tag_message = await self.db.get_tag_message(config_id)
        custom_message = await self.db.get_reply(config_id)

        view = ConfigurePostAssist(
            forum=config["forum_id"],
            tag_message=tag_message,
            custom_msg=custom_message
        )

        await interaction.response.send_message(view=view)
        await view.wait()

        forum = view.forum
        reply = view.custom_msg
        tags = view.tag_list
        tag_message = view.tag_message

        if not (view.tag_list or view.custom_msg):
            return await interaction.followup.send(
                "You must provide either tags or a custom message.",
                ephemeral=True
            )

        if view.finished:
            await interaction.followup.send("Success!", ephemeral=True)
            await self.db.update_configuration(
                id=config_id,
                forum_id=forum,
                entities=tags,
                entity_tag_message=tag_message,
                reply=reply
            )
            return

        await interaction.followup.send("Cancelled.", ephemeral=True)


async def setup(bot: Bot):
    await bot.add_cog(ForumAssist(bot))

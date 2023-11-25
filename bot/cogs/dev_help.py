# pylint: disable = no-member

import asyncio

from discord import Embed, Guild, ForumChannel, Interaction, Thread
from discord.ext.commands.context import Context
from discord.ui import View, Select
from discord.app_commands import command
from discord.ext.commands import Bot, Cog, Context, GroupCog, command as prefixed_command

from database.dev_help import DevHelpTagDB, DevHelpViewsDB
from database.config_auto import Config
from database.settings import Settings
from utils.decorators import is_staff
from ui.views.dev_help import PersistentSolverView


def get_tag_options(db: DevHelpTagDB, forum: ForumChannel) -> View | None:
    """Gets all tag options for the given forum."""

    async def select_callback(interaction: Interaction):
        await db.update("tag_id", int(tag_selection.values[0]))
        await interaction.response.edit_message(
            content=f"Success...",
            view=None
        )
        view.stop()

    view = View()
    tag_selection = Select(placeholder="Select Tag...")
    tag_selection.callback = select_callback

    if not forum.available_tags:
        return

    for a_tag in forum.available_tags:
        tag_selection.add_option(
            label=f"{a_tag.emoji}{a_tag.name}" if a_tag.emoji else a_tag.name, value=a_tag.id
        )

    view.add_item(tag_selection)
    return view


def get_forums(db: Settings, guild: Guild) -> View:
    """Gets all forums."""

    async def select_callback(interaction: Interaction):
        await db.set_setting("dev_help_forum", int(forum_selection.values[0]))
        await interaction.response.edit_message(
            content=f"Success...",
            view=None
        )
        view.stop()

    view = View()
    forum_selection = Select(placeholder="Select Forum...")
    forum_selection.callback = select_callback

    for forum in guild.forums:
        forum_selection.add_option(
            label=forum.name, value=forum.id
        )

    view.add_item(forum_selection)
    return view


class HelpSolver(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.settings = Settings(self.bot.pool)
        self.tag_db = DevHelpTagDB(self.bot.pool)
        self.config = Config(self.bot.pool)
        self.views_db = DevHelpViewsDB(self.bot.pool)

    async def reload_forum(self):
        dev_help = await self.settings.get_setting("dev_help_forum")
        self.forum = self.bot.get_channel(dev_help)

    async def load(self):
        await self.bot.wait_until_ready()
        await self.reload_forum()

        for view in await self.views_db.get_persistent_views():
            self.bot.add_view(
                PersistentSolverView(
                    view["thread_id"],
                    view["author_id"],
                    self.views_db,
                    self.tag_db,
                    self.forum
                ),
            message_id=view["message_id"]
        )

    async def cog_load(self):
        asyncio.create_task(self.load())

    async def cog_check(self, ctx: Context) -> bool:
        channel = ctx.channel

        if not self.forum:
            return False

        if not isinstance(channel, Thread):
            return False

        if not isinstance(channel.parent, ForumChannel):
            return False

        return channel.parent_id == self.forum.id

    @Cog.listener()
    async def on_thread_create(self, thread: Thread):
        config = await self.config.get_config("dev_help")

        if not config["config_status"]:
            return

        settings = await self.tag_db.get()

        if not settings:
            return

        if not self.forum:
            return

        if thread.parent_id != self.forum.id:
            return

        bot_message = await thread.send(
            "Mark this post as Solved!",
            view=PersistentSolverView(
                thread.id,
                thread.owner_id,
                self.views_db,
                self.tag_db,
                self.forum,
            )
        )

        await bot_message.pin()
        await self.views_db.add_view(thread.id, bot_message.id, thread.owner.id)

    @is_staff()
    @command(name="toggle", description="Toggles the dev help feature.")
    async def toggle_config(self, interaction: Interaction):
        """Toggles auto tagging."""

        toggle_map = {
            True: "ON",
            False: "OFF"
        }

        toggle = await self.config.toggle_config("dev_help")

        await interaction.response.send_message(
            f"Turned {toggle_map[toggle]} Dev Help feature.",
            ephemeral=True
        )

    @prefixed_command()
    @is_staff()
    async def solved(self, ctx: Context):
        settings = await self.tag_db.get()
        tag_id = settings["tag_id"]

        if not tag_id:
            return  

        description = "This post has been marked as solved."

        embed = Embed(
            description=description
        )

        tag = ctx.channel.parent.get_tag(tag_id)

        await ctx.channel.add_tags(tag, reason="Solved")
        await ctx.channel.send(embed=embed)

        name = f"[SOLVED] {ctx.channel.name}"

        if len(name) > 100:
            name = name[:97] + "..."

        await ctx.channel.edit(name=name, locked=True)

    @command(name="configure", description="Configure the feature.")
    async def configure(self, interaction: Interaction):
        forum_view = get_forums(self.settings, interaction.guild)
        await interaction.response.send_message(view=forum_view, ephemeral=True)
        await forum_view.wait()

        await self.reload_forum()

        if not self.forum.available_tags:
            return await interaction.followup.send(
                "No tags available for this forum.",
                ephemeral=True
            )

        tag_view = get_tag_options(self.tag_db, self.forum)
        await interaction.followup.send(view=tag_view, ephemeral=True)
        await tag_view.wait()


async def setup(bot: Bot):
    await bot.add_cog(HelpSolver(bot))

# pylint: disable = no-member

import asyncio

from discord import Embed, ForumChannel, Interaction, TextStyle, Thread, NotFound
from discord.ext.commands.context import Context
from discord.ui import Modal, TextInput, View, Select
from discord.app_commands import Choice, choices, command
from discord.ext.tasks import loop
from discord.utils import utcnow
from discord.ext.commands import Bot, Context, GroupCog, command as prefixed_command

from config import GuildInfo
from database.dev_help import DevHelpTagDB


class HelpSolver(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = DevHelpTagDB(self.bot.pool)

    async def load(self):
        await self.bot.wait_until_ready()
        self.forum = self.bot.get_channel(GuildInfo.dev_help_forum)
        self.checker.start()

    async def cog_load(self):
        asyncio.create_task(self.load())

    async def cog_check(self, ctx: Context) -> bool:
        channel = ctx.channel

        if not isinstance(channel, Thread):
            return False

        if not isinstance(channel.parent, ForumChannel):
            return False

        return channel.parent_id == GuildInfo.dev_help_forum

    @loop(minutes=1)
    async def checker(self):
        date = utcnow()
        settings = await self.db.get()

        desc = settings["reminder_message"] or "Reminder to mark your post as solved with `pph-solved`!"
        embed = Embed(description=desc)

        if not self.forum:
            return

        for thread in self.forum.threads:
            messages = [m async for m in thread.history(limit=10)]

            try:
                # NotFound occurs here
                # if the last_message_id is a message of the bot
                last_message = await thread.fetch_message(thread.last_message_id) 

                conditions = (
                    thread.locked,
                    last_message.author.bot,
                    last_message.author == messages[0].author,
                    len(messages) < 5,
                    (date - last_message.created_at).days < 5
                )

                if any(conditions):
                    continue

                await thread.send(embed=embed)

            except NotFound:
                continue

    @prefixed_command()
    async def solved(self, ctx: Context):
        settings = await self.db.get()

        starter_message = await ctx.channel.fetch_message(ctx.channel.id)

        if not settings or (
            not ctx.author.guild_permissions.administrator or
            ctx.author != starter_message.author
        ):
            return

        tag_id = settings["tag_id"]

        if not tag_id:
            return  

        description = settings["custom_message"] or "This post has been marked as solved."

        embed = Embed(
            description=description
        )

        tag = ctx.channel.parent.get_tag(tag_id)

        await ctx.channel.add_tags(tag, reason="Solved")
        await ctx.channel.send(embed=embed)
        await ctx.channel.edit(archived=True, locked=True)

    @command(name="tag", description="The tag to set on a solved post.")
    async def set_tag(self, interaction: Interaction):
        async def select_callback(interaction: Interaction):
            await self.db.update("tag_id", int(tag_selection.values[0]))
            await interaction.response.edit_message(
                content=f"Success...",
                view=None
            )
            view.stop()

        view = View()
        tag_selection = Select(placeholder="Select Tag...")
        tag_selection.callback = select_callback

        if not self.forum.available_tags:
            return await interaction.response.send_message(
                "This forum does not have tags!",
                ephemeral=True
            )

        for a_tag in self.forum.available_tags:
            tag_selection.add_option(
                label=f"{a_tag.emoji}{a_tag.name}", value=a_tag.id
            )

        view.add_item(tag_selection)

        await interaction.response.send_message(
            view=view,
            ephemeral=True
        )

    @command(name="message", description="The custom message to send on a solved post.")
    @choices(
        type=[
            Choice(name="reminder", value="r"),
            Choice(name="closing", value="c")
        ]
    )
    async def set_message(self, interaction: Interaction, type: Choice[str]):
        settings_map = {
            "c": "custom_message",
            "r": "reminder_message"
        }

        async def on_submit(interaction: Interaction):
            embed = Embed(description=text_input.value)
            await self.db.update(settings_map[type.value], text_input.value)
            await interaction.response.send_message("Preview: ", embed=embed, ephemeral=True)

        modal = Modal(title="Custom Message")
        text_input = TextInput(label="Message", style=TextStyle.long)
        modal.add_item(text_input)
        modal.on_submit = on_submit

        await interaction.response.send_modal(modal)
        await modal.wait()


async def setup(bot: Bot):
    await bot.add_cog(HelpSolver(bot))

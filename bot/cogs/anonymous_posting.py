from uuid import UUID

from discord import Interaction, Embed, Guild, Member, TextChannel
from discord.app_commands import Choice, command, describe, choices
from discord.ui import View, Select
from discord.ext.commands import Bot, GroupCog

from database.anonymous_posting import AnonymousPostingDB
from database.config_auto import Config
from utils.decorators import is_staff
from ui.modals.anonymous_posting import AnonymousPost, AnonymousReply
from ui.views.forum_picker import ForumPicker


class AnonymousPosting(GroupCog, name="anon"):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = AnonymousPostingDB(self.bot.pool)
        self.config = Config(self.bot.pool)

    async def _send_to_logs(
        self,
        message: str,
        author: Member,
        guild: Guild
    ):
        """Send a post/reply message to the log channel.

        :param message: The message to send.
        :param author: The post/reply author.
        :param guild: The guild the post has been sent
        """

        channel_id = await self.db.get_log_channel()

        if not channel_id:
            return

        channel_id, = channel_id
        channel = guild.get_channel(channel_id["channel_id"])

        if not channel:
            # If the channel somehow get deleted.
            return

        embed = Embed(description=message)
        embed.set_thumbnail(url=author.display_avatar.url)
        await channel.send(embed=embed)

    @command(name="post", description="Post anonymously on a forum.")
    async def post(self, interaction: Interaction):
        """Post anonymously on a channel."""

        status = await self.config.get_config("anonymous_posting")

        if not status["config_status"]:
            return await interaction.response.send_message(
                "This feature is currently turned off...",
                ephemeral=True
            )

        async def select_callback(interaction: Interaction):
            """The callback to the forum selection view."""

            forum = interaction.guild.get_channel(int(forum_select.values[0]))
            modal = AnonymousPost(forum, self.db)
            await interaction.response.send_modal(modal)
            await modal.wait()
            view.stop()
            await self._send_to_logs(
                (
                    "**New Anonymous Post**\n\n"
                    f"**{modal.post_title}**\n"
                    f"{modal.post_message.value[:1500]}\n\n"
                    f"author: {interaction.user.id} | {interaction.user.mention}\n"
                    f"forum: [{modal.forum}]({modal.forum.jump_url})"
                ),
                interaction.user,
                interaction.guild
            )

        forums = await self.db.get_forums()

        if not forums:
            return await interaction.response.send_message(
                "Allowed forum channels aren't setup yet...",
                ephemeral=True
            )

        view = View()
        forum_select = Select()
        forum_select.callback = select_callback

        for forum in forums:
            forum = interaction.guild.get_channel(
                forum["forum_id"]
            )

            if not forum:
                continue

            forum_select.add_option(
                label=forum.name,
                value=forum.id
            )

        view.add_item(forum_select)
        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()


    @describe(uuid="The UUID of the post to reply to.")
    @command(name="reply", description="Reply anonymously to your forum post.")
    async def reply(self, interaction: Interaction, uuid: str):
        """Reply to a post."""

        status = await self.config.get_config("anonymous_posting")

        if not status["config_status"]:
            return await interaction.response.send_message(
                "This feature is currently turned off...",
                ephemeral=True
            )

        forums = await self.db.get_forums()

        if not forums:
            return await interaction.response.send_message(
                "Allowed forum channels aren't setup yet...",
                ephemeral=True
            )

        posts = await self.db.get_posts(interaction.user.id)

        if uuid not in [str(post['post_uuid']) for post in posts]:
            return await interaction.response.send_message(
                "This post doesn't exist.",
                ephemeral=True
            )

        uuid = UUID(uuid)
        post, = await self.db.get_post(uuid)
        thread = interaction.guild.get_thread(post["post_id"])
        modal = AnonymousReply(thread)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self._send_to_logs(
            (
                f"**Anonymous Reply to: [{thread}]({thread.jump_url})**\n\n"
                f"{modal.post_message.value[:1500]}\n\n"
                f"author: {interaction.user.id} | {interaction.user.mention}\n"
                f"forum: [{modal.thread}]({modal.thread.jump_url})"
            ),
            interaction.user,
            interaction.guild
        )

    @is_staff()
    @command(name="toggle", description="Reply anonymously to your forum post.")
    async def toggle(self, interaction: Interaction):
        """Toggles the feature."""

        toggle_map = {
            True: "ON",
            False: "OFF"
        }

        toggle = await self.config.toggle_config("anonymous_posting")

        await interaction.response.send_message(
            f"Turned {toggle_map[toggle]} Anonymous Posting.",
            ephemeral=True
        )

    @is_staff()
    @describe(action="The action to take.")
    @command(name="forums", description="View allowed forums.")
    @choices(
        action=[
            Choice(name="Add", value="add"),
            Choice(name="Remove", value="remove"),
            Choice(name="View All", value="view")
        ]
    )
    async def forums(self, interaction: Interaction, action: Choice[str]):
        """Add/Remove/View allowed forums to the database.

        :param action: The action to take.
        """

        action = action.value

        if action == "add":
            view = ForumPicker()

            await interaction.response.send_message(
                "Select forums...",
                view=view,
                ephemeral=True
            )
            await view.wait()

            forum_ids = [forum.id for forum in view.forums]

            await self.db.add_forums(forum_ids)

        elif action == "remove":
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
            await interaction.response.send_message(view=view, ephemeral=True)
            await view.wait()
            await self.db.remove_forums(map(int, select.values))

        else:
            embed = Embed(
                title=f"All Forums allowed for Anonymous Posting"
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

    @is_staff()
    @command(name="setlogs", description="Set the logging channel.")
    async def set_logs(self, interaction: Interaction, channel: TextChannel):
        """Set the logging channel for this feature"""

        await self.db.upsert_log_channel(channel.id)
        await interaction.response.send_message(
            f"Logging channel set to {channel.mention} | {channel.id}",
            ephemeral=True
        )


async def setup(bot: Bot):
    await bot.add_cog(AnonymousPosting(bot))

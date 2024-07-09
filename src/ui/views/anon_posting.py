from discord import Interaction
from discord.ui import View, Select, Button, button
from discord.ext.commands import Cog

from src.data.admin.config_auto import Config
from src.ui.modals.anonymous_posting import AnonymousPost, AnonymousReply


class PersistentAnonView(View):
    def __init__(
            self,
            salt: str,
            cog: Cog,
            config: Config,
            timeout: int = None
        ):
        self.cog = cog
        self.config = config
        self.salt = salt
        super().__init__(timeout=timeout)

    @button(label="Create Post", custom_id="persistent: post")
    async def button_callback(self, interaction: Interaction, button: Button):
        status = await self.config.get_config("anonymous_posting")

        if not status["config_status"]:
            return await interaction.response.send_message(
                "This feature is currently turned off...",
                ephemeral=True
            )

        async def select_callback(interaction: Interaction):
            """The callback to the forum selection view."""

            forum = interaction.guild.get_channel(int(forum_select.values[0]))
            modal = AnonymousPost(forum, self.salt, from_button=True)
            await interaction.response.send_modal(modal)
            await modal.wait()
            view.stop()

            if not modal.success:
                return

            await self.cog._send_to_logs(
                (
                    "**New Anonymous Post**\n\n"
                    f"**{modal.post_title}**\n"
                    f"{modal.post_message.value[:1500]}\n\n"
                    f"author: {interaction.user.id} | {interaction.user.mention}\n"
                    f"forum: [{modal.forum}]({modal.forum.jump_url})\n"
                    f"thread: [{modal.thread}]({modal.thread.jump_url})"
                ),
                interaction.user,
                interaction.guild
            )

        forums = await self.cog.db.get_forums()

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

    @button(label="Reply to a Post", custom_id="persistent: reply")
    async def reply_button_callback(self, interaction: Interaction, button: Button):
        status = await self.config.get_config("anonymous_posting")

        if not status["config_status"]:
            return await interaction.response.send_message(
                "This feature is currently turned off...",
                ephemeral=True
            )

        modal = AnonymousReply(self.salt)
        await interaction.response.send_modal(modal)
        await modal.wait()

        if not modal.success:
            return

        await self.cog._send_to_logs(
            (
                f"**Anonymous Reply to: [{modal.thread}]({modal.thread.jump_url})**\n\n"
                f"{modal.post_message.value[:1700]}\n\n"
                f"author: {interaction.user.id} | {interaction.user.mention}\n"
                f"forum: [{modal.thread.parent}]({modal.thread.parent.jump_url})"
            ),
            interaction.user,
            interaction.guild
        )

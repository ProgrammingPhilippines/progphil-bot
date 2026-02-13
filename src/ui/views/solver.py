from discord import ButtonStyle, Embed, ForumChannel, Interaction, Thread
from discord.ui import Button, Select, View, button
from discord.ui.item import Item

from ...data.forum.post_assist import PostAssistDB
from ...utils.logging.logger import Logger


class PersistentSolverView(View):
    def __init__(
        self,
        thread_id: int,
        author_id: int,
        db: PostAssistDB,
        staff_roles: list[int],
        logger: Logger,
    ):
        self.thread_id = thread_id
        self.author_id = author_id
        self.db = db
        self.staff_roles = staff_roles
        self.logger = logger
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: Interaction) -> bool:
        conditions = (
            interaction.user.id == self.author_id,
            interaction.user.guild_permissions.administrator,
            any(
                interaction.guild.get_role(role) in interaction.user.roles
                for role in self.staff_roles
            ),
        )

        if not any(conditions):
            await interaction.response.send_message(
                "This isn't for you!", ephemeral=True
            )
            self.logger.info(
                f"User {interaction.user.id} tried to use a view they don't own."
            )
            return False
        return True

    @button(label="Solved!", style=ButtonStyle.green, custom_id="solved")
    async def solved(self, interaction: Interaction, button: Button):
        self.stop()
        await interaction.response.defer()

        thread = (
            interaction.guild.get_thread(self.thread_id) if interaction.guild else None
        )

        if not thread:
            fetched = await interaction.client.fetch_channel(self.thread_id)
            thread = fetched if isinstance(fetched, Thread) else None

        if not thread or not isinstance(thread.parent, ForumChannel):
            await interaction.followup.send(
                "Could not resolve this thread anymore.",
                ephemeral=True,
            )
            return

        bot_user_id = interaction.client.user.id if interaction.client.user else 0

        users = {
            (message.author.display_name, message.author.id)
            async for message in thread.history(limit=None)
            if message.author.id != bot_user_id and message.author.id != self.author_id
        }

        message = "This post has been marked as solved."
        view = None

        if users:

            async def selection_callback(interaction: Interaction):
                await interaction.response.send_message("Thanks!", ephemeral=True)
                view.stop()

            async def cancel_callback(interaction: Interaction):
                await interaction.response.send_message("Cancelled!", ephemeral=True)
                view.stop()

            view = View(timeout=60)
            selection = Select(
                placeholder="Select users that helped you solve your problem.",
                max_values=len(users),
            )
            cancel = Button(label="Cancel", style=ButtonStyle.red)
            cancel.callback = cancel_callback
            selection.callback = selection_callback

            for name, id in users:
                selection.add_option(label=name, value=str(id))

            view.add_item(selection)
            view.add_item(cancel)

            await interaction.followup.send(view=view, ephemeral=True)
            await view.wait()

            if selection.values:
                members = [thread.guild.get_member(int(id)) for id in selection.values]
                mentions = [member.mention for member in members if member is not None]
                mentions_str = ", ".join(mentions)

                if len(mentions) > 1:
                    message += f" Thanks to the following users: {mentions_str}"
                else:
                    message += f" Thanks to {mentions_str}"

        embed = Embed(description=message)

        tag_id = await self.db.get_mark_as_solved_tag(thread.parent_id)
        tag = thread.parent.get_tag(tag_id) if tag_id else None

        name = f"[SOLVED] {thread.name}"
        self.logger.info(name)

        if len(name) > 100:
            name = name[:97] + "..."

        await thread.edit(locked=True, name=name)
        if tag:
            await thread.add_tags(tag, reason="Solved")
        await thread.send(embed=embed)
        await self.db.close_persistent_mark_as_solved_view(thread.id)

    async def on_error(
        self,
        interaction: Interaction,
        error: Exception,
        item: Item,
    ) -> None:
        info = f"Thread ID: {self.thread_id}"
        self.logger.error(
            f"An error occurred while using the solve button:\n```{error}\n{info}```"
        )

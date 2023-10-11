from discord import ButtonStyle, Interaction, ForumChannel
from discord.ui import View, Button, button

from database.dev_help import DevHelpViewsDB, DevHelpTagDB


class PersistentSolverView(View):
    def __init__(
        self,
        message_id: int,
        author_id: int,
        db: DevHelpViewsDB,
        tag_db: DevHelpTagDB,
        forum: ForumChannel
    ):
        self.message_id = message_id
        self.author_id = author_id
        self.db = db
        self.tag_db = tag_db
        self.forum = forum
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: Interaction) -> bool:
        if not interaction.user.id == self.author_id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return False
        return True

    @button(label="Solved!", style=ButtonStyle.green, custom_id="solved")
    async def solved(self, interaction: Interaction, button: Button):
        settings = await self.tag_db.get()
        thread = self.forum.get_thread(self.message_id)
        tag = thread.parent.get_tag(settings["tag_id"])
        await thread.add_tags(tag, reason="Solved")
        await thread.edit(name=f"[SOLVED] {thread.name}", locked=True)
        await thread.send("This post has been marked as solved.")
        await self.db.close_view(thread.id)
        await interaction.response.send_message("Solved!", ephemeral=True)
        self.stop()

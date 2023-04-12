from uuid import uuid4

from discord import Interaction, ForumChannel, TextStyle, Thread
from discord.ui import Modal, TextInput, View, Select

from database.anonymous_posting import AnonymousPostingDB


class AnonymousPost(Modal, title="Anonymous Post"):
    post_title = TextInput(
        label="Title",
        placeholder="Enter title..."
    )
    post_message = TextInput(
        label="Message",
        placeholder="Enter message...",
        style=TextStyle.long
    )

    def __init__(self, forum: ForumChannel, db: AnonymousPostingDB):
        self.forum = forum
        self.db = db
        super().__init__()

    async def on_submit(self, interaction: Interaction) -> None:
        if self.forum.flags.require_tag:
            async def select_callback(interaction: Interaction):
                await interaction.response.edit_message(
                    content=f"Selected {len(tag_selection.values)} tags...",
                    view=None
                )
                view.stop()

            max_vals = len(self.forum.available_tags)

            if max_vals > 25:
                max_vals = 25

            view = View()
            tag_selection = Select(
                placeholder="Select Tags...",
                max_values=max_vals
            )
            tag_selection.callback = select_callback

            for a_tag in self.forum.available_tags:
                tag_selection.add_option(
                    label=f"{a_tag.emoji}{a_tag.name}", value=a_tag.id
                )

            view.add_item(tag_selection)
            await interaction.response.send_message(
                "There seems to be a required tag on the selected forum.",
                view=view,
                ephemeral=True
            )
            await view.wait()

            forum_tags = []

            for tag in tag_selection.values:
                tag = self.forum.get_tag(int(tag))
                if tag:
                    forum_tags.append(tag)

            thread = await self.forum.create_thread(
                name=self.post_title.value,
                content=self.post_message.value,
                applied_tags=forum_tags
            )

        else:
            thread = await self.forum.create_thread(
                name=self.post_title.value,
                content=self.post_message.value
            )

        uuid = uuid4()
        thread_id = thread.thread.id
        author_id = interaction.user.id

        await self.db.insert_post(
            uuid,
            thread_id,
            author_id,
            self.post_title.value
        )

        success_message = (
            f"Successfully posted! here is your post UUID:\n**{uuid}**\n\n"
            "Make sure not to lose that, you can use that to reply "
            "to your original post using `/anonymous-posting reply`"
        )

        if interaction.response.is_done():
            await interaction.followup.send(success_message, ephemeral=True)
        else:
            await interaction.response.send_message(success_message, ephemeral=True)


class AnonymousReply(Modal, title="Anonymous Reply"):
    post_message = TextInput(
        label="Message",
        placeholder="Enter message...",
        style=TextStyle.long
    )

    def __init__(self, thread: Thread):
        self.thread = thread
        super().__init__()

    async def on_submit(self, interaction: Interaction) -> None:
       await self.thread.send(self.post_message.value)
       await interaction.response.send_message("Success...", ephemeral=True)

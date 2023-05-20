from base64 import b64encode

from cryptography.fernet import Fernet, InvalidToken
from discord import Embed, Interaction, ForumChannel, TextStyle, Thread, Forbidden
from discord.ui import Modal, TextInput, View, Select


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

    def __init__(self, forum: ForumChannel, salt: str):
        self.forum = forum
        self.salt = salt
        self.success: bool = False
        super().__init__()

    async def on_submit(self, interaction: Interaction) -> None:
        post_title = self.post_title.value
        post_message = self.post_message.value

        if post_title.isspace():
            post_title = "Empty title..."

        if post_message.isspace():
            post_message = "Empty message..."

        if self.forum.flags.require_tag:
            async def select_callback(interaction: Interaction):
                await interaction.response.edit_message(
                    content=f"Selected {len(tag_selection.values)} tag(s)...",
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

            thread_message = await self.forum.create_thread(
                name=post_title,
                content=post_message,
                applied_tags=forum_tags
            )

        else:
            thread_message = await self.forum.create_thread(
                name=post_title,
                content=post_message
            )

        self.thread = thread_message.thread
        thread_id = self.thread.id
        author_id = interaction.user.id
        key = b64encode(f"{author_id}{self.salt}"[:32].encode())

        fernet = Fernet(key)
        encrypted = fernet.encrypt(f"{thread_id} {author_id}".encode())

        success_message = (
            f"Hello {interaction.user.mention},\n"
            f"Here is your reply key for your anonymous post {thread_message.thread.jump_url}. Use the command `/anon reply` with this key to anonymously reply to it\n"
            f"```{encrypted.decode()}```\n"
            "Do not share this with other users."
        )

        embed = Embed(
            description=success_message
        )

        await interaction.user.send(embed=embed)

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

        self.success = True


class AnonymousReply(Modal, title="Anonymous Reply"):
    encrypted_post = TextInput(
        label="Post Ciphertext",
        placeholder="The key of your post."
    )
    post_message = TextInput(
        label="Message",
        placeholder="Enter message...",
        style=TextStyle.long
    )

    def __init__(self, salt: str):
        self.salt = salt
        self.thread: Thread | None = None
        self.success: bool = False
        super().__init__()

    async def on_submit(self, interaction: Interaction) -> None:
        post_message = self.post_message.value

        if post_message.isspace():
            post_message = "Empty reply..."

        key = b64encode(f"{interaction.user.id}{self.salt}"[:32].encode())
        fernet = Fernet(key)

        try:
            decrypted = fernet.decrypt(self.encrypted_post.value)
        except InvalidToken:
            return await interaction.response.send_message(
                "Reply failed. Did you write the correct ciphertext for your post?",
                ephemeral=True
            )

        thread_id, _ = decrypted.decode().split()
        self.thread = interaction.guild.get_thread(int(thread_id))

        if not self.thread:
            return

        await self.thread.send(post_message)
        await interaction.response.send_message("Success...", ephemeral=True)
        self.success = True

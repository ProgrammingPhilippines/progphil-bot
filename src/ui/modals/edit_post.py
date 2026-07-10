from discord import Interaction
from discord.enums import TextStyle
from discord.ext.commands.bot import Bot
from discord.ui.modal import Modal
from discord.ui.text_input import TextInput


class EditPostModal(Modal, title="Edit post"):
    message = TextInput(
        label="Content",
        placeholder="...",
        required=True,
        style=TextStyle.long,
        max_length=4000,
    )

    def __init__(self, channel_id: int, post_id: int, original_content: str, bot: Bot):
        super().__init__()

        self.bot = bot
        self.channel_id = channel_id
        self.post_id = post_id
        self.message.default = original_content

    async def on_submit(self, interaction: Interaction, /) -> None:
        channel = await self.bot.fetch_channel(self.channel_id)
        message = await channel.fetch_message(self.post_id)
        await message.edit(content=self.message.value)
        await interaction.response.send_message("Post edited.", ephemeral=True)

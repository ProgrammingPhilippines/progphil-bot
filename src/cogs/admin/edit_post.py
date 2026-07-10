from discord import Interaction, Message, NotFound
from discord.app_commands import command
from discord.app_commands.commands import describe
from discord.ext.commands.bot import Bot
from discord.ext.commands.cog import Cog, GroupCog

from data.admin.config_auto import Config
from ui.modals.edit_post import EditPostModal
from utils.decorators import is_staff


class EditPost(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Config(self.bot.pool)

    @is_staff()
    @command(
        name="post-edit",
        description="A command to allow staff to edit an existing post created by the PPH bot",
    )
    @describe(message_id="The ID post/message to edit")
    async def edit_post(self, interaction: Interaction, message_id: str):

        if not interaction.channel_id:
            return

        try:
            message = await interaction.channel.fetch_message(int(message_id))
        except (ValueError, NotFound):
            await interaction.response.send_message(
                "Message not found in this channel.", ephemeral=True
            )
            return

        if self.bot.user is not None and message.author.id != self.bot.user.id:
            await interaction.response.send_message(
                "Cannot edit message that isn't from PPH bot!", ephemeral=True
            )
            return

        post_id = message.id
        content = message.content
        edit_post_modal = EditPostModal(
            channel_id=interaction.channel_id,
            post_id=post_id,
            original_content=content,
            bot=self.bot,
        )

        await interaction.response.send_modal(edit_post_modal)


async def setup(bot: Bot):
    await bot.add_cog(EditPost(bot))

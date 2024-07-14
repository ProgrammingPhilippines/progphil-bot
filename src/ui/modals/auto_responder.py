from discord import Interaction, TextStyle
from discord.ext.commands import Bot
from discord.ui import Modal, TextInput

from ...data.auto_responder import AutoRespondDB
from ...ui.views.auto_responder import AutoResponderSelect


class AutoResponder(Modal, title="Auto Responder"):
    message = TextInput(
        label='Trigger Message',
        placeholder='Type a word or phrase...',
        required=True,
    )
    response = TextInput(
        label='Response',
        placeholder='Type the response...',
        required=True,
        style=TextStyle.paragraph
    )

    def __init__(self, db: AutoRespondDB, response_type: str, matching_type: str, bot: Bot):
        self.db = db
        self.bot = bot
        self.response_type = response_type
        self.matching_type = matching_type

        if matching_type == 'regex':
            self.message.label = 'Regex'
            self.message.placeholder = 'Type a regex pattern...'

        super().__init__()

    async def on_submit(self, interaction: Interaction) -> None:
        view = AutoResponderSelect(
            self.db,
            [channel for guild in self.bot.guilds for channel in guild.text_channels],
            self
        )
        await interaction.response.send_message(view=view, ephemeral=True)

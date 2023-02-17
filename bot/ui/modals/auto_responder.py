from discord import Interaction, TextStyle
from discord.ui import Modal, TextInput
from database.auto_responder import AutoRespondDB


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

    def __init__(self, db: AutoRespondDB, response_type: str):
        self.db = db
        self.response_type = response_type
        super().__init__()

    async def on_submit(self, interaction: Interaction) -> None:
        await self.db.insert_response(
            self.message.value.strip(),
            self.response.value.strip(),
            self.response_type
        )

        await interaction.response.send_message("Success.", ephemeral=True)

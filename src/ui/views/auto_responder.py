from typing import List, Any

from src.data.auto_responder import AutoRespondDB
from discord import Embed, Interaction, TextChannel, ChannelType
from discord.ui import View, Button, button, ChannelSelect


def _format_description(data: dict) -> str:
    description = ""

    for num, response in enumerate(data, start=1):
        description += (
            f"{num}. **{response['message']}**\n"
            f"```ID: {response['id']}\n"
            f"Response: {response['response']}\n"
            f"Response Type: {response['response_type']}\n"
            f"Matching Type: {response['matching_type']}```"
        )

    return description


class AutoResponderPagination(View):
    """The view for checking auto responder items.

    :param db: The auto responder db.
    :param chunk_count: The count of all pages.
    """

    def __init__(
            self,
            db: AutoRespondDB,
            chunk_count: int
    ):
        self.offset = 0
        self.title = "**All automated responses.**\n"
        self.db = db
        self.chunk_count = chunk_count
        super().__init__(timeout=180)

    @button(label="Previous", disabled=True)
    async def previous_button(self, interaction: Interaction, button: Button):
        """This button will be disabled at first, but will be
        re-enabled when the user clicks "Next".
        """

        embed = Embed()
        self.next_button.disabled = False
        self.offset -= 5

        if self.offset < 5:
            # Disable the button if the page is back to 1
            button.disabled = True

        description = f"Page {self.offset // 5 + 1}/{self.chunk_count}\n"
        data = await self.db.get_responses(self.offset)

        description += _format_description(data)

        embed.description = self.title + description
        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="Next")
    async def next_button(self, interaction: Interaction, button: Button):
        """This button will handle the next page of the view."""

        embed = Embed()
        self.previous_button.disabled = False
        self.offset += 5

        # Disable this button if the page reaches the max number of pages.
        if self.offset // 5 + 1 >= self.chunk_count:
            button.disabled = True

        description = f"Page {self.offset // 5 + 1}/{self.chunk_count}\n"
        data = await self.db.get_responses(self.offset)

        description += _format_description(data)

        embed.description = self.title + description
        await interaction.response.edit_message(embed=embed, view=self)


class ResponderChannelSelect(ChannelSelect):
    def __init__(self, **kwargs):
        super().__init__(
            placeholder="Select a channel...",
            channel_types=[ChannelType.text],
            min_values=0,
            **kwargs
        )

    async def callback(self, interaction: Interaction) -> Any:
        await interaction.response.defer()


class AutoResponderSelect(View):
    def __init__(self, db: AutoRespondDB, channels: List[TextChannel], modal: "AutoResponder"):
        super().__init__(timeout=180)
        self.db = db
        self.channels = channels
        self.modal = modal
        self.select = ResponderChannelSelect(max_values=len(self.channels) if len(self.channels) < 25 else 25)
        self.add_item(self.select)

    @button(label="Cancel")
    async def cancel_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_message("Cancelled!", ephemeral=True)
        self.stop()

    @button(label="Submit")
    async def submit_button(self, interaction: Interaction, button: Button):
        response_id = await self.db.insert_response(
            self.modal.message.value.strip().lower(),
            self.modal.response.value.strip(),
            self.modal.response_type,
            self.modal.matching_type,
            len(self.select.values) > 0
        )

        for channel in self.select.values:
            await self.db.insert_channel_response(channel.id, int(response_id))

        await interaction.response.send_message("Response added!", ephemeral=True)
        self.stop()

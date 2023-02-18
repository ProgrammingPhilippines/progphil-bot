from discord import Embed, Interaction
from discord.ui import View, Button, button

from database.auto_responder import AutoRespondDB


def _format_description(data: dict) -> str:
    description = ""

    for num, response in enumerate(data, start=1):
        description += (
            f"{num}. **{response['message']}**\n"
            f"```ID: {response['id']}\n"
            f"Response: {response['response']}\n"
            f"Response Type: {response['response_type']}```\n"
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

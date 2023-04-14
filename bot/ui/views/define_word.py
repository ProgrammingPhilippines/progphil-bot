from typing import Tuple, List

from discord import Embed, Interaction, ButtonStyle, User
from discord.ui import View, Button, button


class DefineWordPagination(View):
    def __init__(
        self,
        word: str,
        user: User,
        data: List[Tuple[str, str]]
    ):
        self.offset = 0
        self.user = user
        self.word = word
        self.data = data
        super().__init__(timeout=180)

    async def interaction_check(self, interaction):
        if interaction.user != self.user:
            await interaction.response.send_message(
                "You do not own this view.",
                ephemeral=True
            )
        return interaction.user == self.user

    @button(label="Previous", disabled=True)
    async def previous_button(self, interaction: Interaction, button: Button):
        """This button will be disabled at first, but will be
        re-enabled when the user clicks "Next".
        """

        embed = Embed()
        self.next_button.disabled = False
        self.offset -= 1

        if self.offset < 1:
            # Disable the button if the page is back to 1
            button.disabled = True

        embed.title = f"Definition for {self.word}"
        embed.description = f"`[{self.data[self.offset][0].upper()}]` - {self.data[self.offset][1]}"

        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="Next")
    async def next_button(self, interaction: Interaction, button: Button):
        """This button will be disabled at first, but will be
        re-enabled when the user clicks "Previous".
        """

        embed = Embed()
        self.previous_button.disabled = False
        self.offset += 1

        if self.offset > len(self.data) - 2:
            # Disable the button if the page is the last page
            button.disabled = True

        embed.title = f"Definition for {self.word}"
        embed.description = f"`[{self.data[self.offset][0].upper()}]` - {self.data[self.offset][1]}"

        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="Close", style=ButtonStyle.red)
    async def close_button(self, interaction: Interaction, button: Button):
        """This button will be disabled at first, but will be
        re-enabled when the user clicks "Previous".
        """

        await interaction.response.edit_message(view=None)

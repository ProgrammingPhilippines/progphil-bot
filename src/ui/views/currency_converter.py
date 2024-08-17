from typing import Tuple, List

from discord import Embed, Interaction, ButtonStyle, User
from discord.ui import View, Button, button
from logging import Logger


class CurrencyConverterPagination(View):
    """The view for checking currency converter items.

    :param user: The user who owns the view.
    :param data: The data to display.
    """

    def __init__(
        self,
        user: User,
        data: List[Tuple[str, str]],
        logger: Logger,
    ):
        self.offset = 0
        self.title = "**Here are the available currencies**\n"
        self.user = user
        self.data = data
        self.logger = logger
        super().__init__(timeout=180)

    async def interaction_check(self, interaction):
        if interaction.user != self.user:
            self.logger.info(f"{interaction.user} tried to use {self.user}'s view.")
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
        self.offset -= 10

        if self.offset < 10:
            # Disable the button if the page is back to 1
            button.disabled = True

        embed.title = self.title
        embed.description = ""

        for i in range(self.offset, self.offset + 10):
            if i >= len(self.data):
                break

            embed.description += f"{self.data[i][0]} - {self.data[i][1]}\n"

        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="Next")
    async def next_button(self, interaction: Interaction, button: Button):
        """This button will be disabled at first, but will be
        re-enabled when the user clicks "Previous".
        """

        embed = Embed()
        self.previous_button.disabled = False
        self.offset += 10

        if self.offset > len(self.data) - 10:
            # Disable the button if the page is the last page
            button.disabled = True

        embed.title = self.title
        embed.description = ""

        for i in range(self.offset, self.offset + 10):
            if i >= len(self.data):
                break

            embed.description += f"{self.data[i][0]} - {self.data[i][1]}\n"

        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="Close", style=ButtonStyle.red)
    async def close_button(self, interaction: Interaction, button: Button):
        """This button will be disabled at first, but will be
        re-enabled when the user clicks "Previous".
        """

        await interaction.response.edit_message(view=None)

from math import ceil

from discord import Interaction, Embed, Message
from discord.ui import Select, View
from discord.app_commands import Choice, command, describe, choices
from discord.ext.commands import Bot, Cog

from database.auto_responder import AutoRespondDB
from utils.decorators import is_staff
from ui.modals.auto_responder import AutoResponder
from ui.views.auto_responder import AutoResponderPagination


class Responder(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.db = AutoRespondDB(self.bot.pool)

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        auto_resps = await self.db.get_responses()

        # Loops over all responses
        # If a certain trigger gets matched within the message,
        # Send a response based on the response type.
        for response in auto_resps:
            is_phrase = False
            # Checks if a trigger message is a phrase
            if len(response["message"].split()) > 1:
                is_phrase = True

            if is_phrase:
                condition = response["message"] in message.content

            else:
                condition = response["message"] in message.content.split()

            if condition:
                if response["rtype"] == "reply":
                    await message.reply(
                        response["response"]
                    )
                else:
                    await message.channel.send(
                        response["response"]
                    )
                break

    @is_staff()
    @command(name="addresponse",
             description="Adds an automated response to a certain message")
    @describe(response_type="Determines if the chat should be regular or a reply.")
    @choices(
        response_type=[
            Choice(name="reply", value="reply"),
            Choice(name="regular", value="regular")
        ]
    )
    async def add_response(self, interaction: Interaction, response_type: Choice[str]):
        """Adds an automated response to a certain message.

        :param response_type: The response type.
        """

        modal = AutoResponder(self.db, response_type.value)
        await interaction.response.send_modal(modal)
        await modal.wait()

    @is_staff()
    @command(name="viewresponses",
             description="Gets all automated responses.")
    async def view_responses(self, interaction: Interaction):
        """Gets all automated responses and their messages."""

        embed = Embed(
            description="**All automated responses.**\n"
        )

        data = await self.db.get_responses(0)

        # loop over the list of responses and parse.
        if len(data) >= 1:
            count = await self.db.records_count()
            page_count = ceil(count / 5)
            description = f"Page 1/{page_count}\n"

            for num, response in enumerate(data, start=1):
                description += (
                    f"{num}. **{response['message']}**"
                    f"```Response: {response['response']}\nResponse Type: {response['rtype']}```\n"
                )

            embed.description = description
            view = AutoResponderPagination(self.db, page_count)

            if page_count < 2:
                # Disables all buttons if there is only 1 page.
                for button in view.children:
                    button.disabled = True

            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )
        else:
            embed.description = "Nothing yet..."
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @is_staff()
    @command(name="deleteresponse",
             description="Deletes a selected response.")
    async def delete_responses(self, interaction: Interaction):
        """Deletes a selected response"""

        records_count = await self.db.records_count()

        if records_count < 1:
            await interaction.response.send_message(
                "There is no data to remove!",
                ephemeral=True
            )

        if records_count > 25:
            # The max items you can select on the selection
            # is 25, so we set it to 25 if it grows more than that
            records_count = 25

        async def select_callback(interaction: Interaction):
            """This callback gets called after the selection is done."""

            for selected in selection.values:
                await self.db.delete_response(int(selected))

            await interaction.response.edit_message(
                content="Deletion finished.",
                view=None
            )

        view = View()
        selection = Select(
            placeholder="Select items...",
            max_values=records_count
        )

        selection.callback = select_callback

        # Dynamically adds the options from the database.
        for response in await self.db.get_responses():
            selection.add_option(
                label=response["message"],
                value=response["id"]
            )

        view.add_item(selection)
        await interaction.response.send_message(
            "Pick the custom responses you want to delete.",
            view=view,
            ephemeral=True
        )


async def setup(bot: Bot):
    await bot.add_cog(Responder(bot))

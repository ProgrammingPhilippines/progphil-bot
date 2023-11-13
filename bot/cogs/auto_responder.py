import re
from math import ceil

from discord import Interaction, Embed, Message
from discord.app_commands import Choice, command, describe, choices
from discord.ext.commands import Bot, Cog, GroupCog
from fuzzywuzzy import fuzz

from database.auto_responder import AutoRespondDB
from ui.modals.auto_responder import AutoResponder
from ui.views.auto_responder import AutoResponderPagination
from utils.decorators import is_staff


class Responder(GroupCog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.db = AutoRespondDB(self.bot.pool)

    @staticmethod
    def __match(message: str, trigger: str, matching_type: str) -> bool:
        """Checks if the message matches the trigger.

        :param message: The message to check.
        :param trigger: The trigger to check.
        :param matching_type: The matching type.
        :return: True if the message matches the trigger, False otherwise.
        """

        if matching_type == "strict":
            return message == trigger

        if matching_type == "strict_contains":
            return trigger in message

        if matching_type == "lenient":
            return fuzz.ratio(message.lower(), trigger) >= 90

        if matching_type == "regex":
            pattern = re.compile(r'{}'.format(trigger))
            return pattern.match(message.lower()) is not None

        return False

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        auto_resps = await self.db.get_responses()

        # Loops over all responses
        # If a certain trigger gets matched within the message,
        # Send a response based on the response type.
        for response in auto_resps:
            if not self.__match(
                message.content,
                response["message"],
                response["matching_type"]
            ):
                continue

            channels = await self.db.get_response_channels(response["id"])

            if response["specified"] and message.channel.id not in channels:
                continue

            if response["response_type"].strip() == "reply":
                await message.reply(response["response"])
                continue

            await message.channel.send(response["response"])
            break

    @is_staff()
    @command(name="add",
             description="Adds an automated response to a certain message")
    @describe(response_type="Determines if the chat should be regular or a reply.")
    @choices(
        response_type=[
            Choice(name="reply", value="reply"),
            Choice(name="regular", value="regular")
        ],
        matching_type=[
            Choice(name="strict", value="strict"),
            Choice(name="strict contains", value="strict_contains"),
            Choice(name="lenient", value="lenient"),
            Choice(name="regex", value="regex")
        ]
    )
    async def add_response(self, interaction: Interaction, response_type: Choice[str], matching_type: Choice[str]):
        """Adds an automated response to a certain message.

        :param interaction: Discord interaction.
        :param response_type: The response type.
        :param matching_type: The matching type.
        """

        modal = AutoResponder(self.db, response_type.value, matching_type.value, self.bot)
        await interaction.response.send_modal(modal)
        await modal.wait()

    @is_staff()
    @command(name="all",
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
                    f"{num}. **{response['message']}**\n"
                    f"```ID: {response['id']}\n"
                    f"Response: {response['response']}\n"
                    f"Response Type: {response['response_type']}```\n"
                )

            embed.description = description
            view = AutoResponderPagination(self.db, page_count)

            if page_count < 2:
                # Disables all buttons if there is only 1 page.
                view.next_button.disabled = True

            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )
        else:
            embed.description = "Nothing yet..."
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @is_staff()
    @command(name="delete",
             description="Deletes a selected response.")
    async def delete_responses(self, interaction: Interaction, response_id: int):
        """Deletes a selected response"""

        records_count = await self.db.records_count()

        if records_count < 1:
            await interaction.response.send_message(
                "There is no data to remove!",
                ephemeral=True
            )

        is_deleted = await self.db.delete_response(response_id)

        if is_deleted:
            message = "Deleted Successfully."
        else:
            message = f"There was a problem deleting #{response_id}. It may not exist."

        await interaction.response.send_message(message, ephemeral=True)


async def setup(bot: Bot):
    await bot.add_cog(Responder(bot))

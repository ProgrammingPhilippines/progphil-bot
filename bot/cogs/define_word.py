import requests
import discord
from discord.ext.commands import Bot
from discord.app_commands import command, describe
from discord.ext.commands import GroupCog

from utils.decorators import is_staff


class Define(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.command_enabled = True

    @command(name="word", description="Give Dictionary Definition to the Given Word")
    @describe(word="The Word that will be Defined")
    async def define(
        self,
        interaction: discord.Interaction,
        word: str,
    ) -> None:
        """
        Give Dictionary Definition to the Given Word

        :param interaction: Interaction
        :param word: The Word to Define
        """

        if not self.command_enabled:
            await interaction.response.send_message("Sorry, this command is currently disabled.")
            return

        url = "https://api.dictionaryapi.dev/api/v2/entries/en/" + word
        response = requests.get(url)

        if "title" in response.json() and response.json()["title"] == "No Definitions Found":
            respond_message = response.json()['message']
        else:
            definitions = ''

            for words in response.json():
                for meaning in words['meanings']:
                    for definition in meaning['definitions']:
                        definitions += definition['definition'] + '\n'

            respond_message = f"Here's what i got on the Word {word} \n\n {definitions}"
        await interaction.response.send_message(respond_message)

    # Command to Turn this Command On or Off
    @is_staff()
    @command(name="toggle", description="Turn Define Command On/Off")
    async def toggle(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """
        Turn Define Command On/Off

        :param interaction: Interaction
        """

        if self.command_enabled:
            self.command_enabled = False
            response = "Command is now Disabled"
        else:
            self.command_enabled = True
            response = "Command is now Enabled"

        await interaction.response.send_message(response)


async def setup(bot: Bot):
    await bot.add_cog(Define(bot))

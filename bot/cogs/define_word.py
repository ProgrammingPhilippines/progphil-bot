import requests
import discord
from discord.ui import Button, View
from discord import Embed
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
            message = response.json()['message']
            respond_message = Embed(
                title=word,
                description=message,
                color=discord.Color.blurple()
            )
            await interaction.response.send_message(embed=respond_message) 
            return
        else:
            definitions = ''
            defs = []
            num = 1
            for words in response.json():
                for meaning in words['meanings']:
                    for definition in meaning['definitions']:
                        part_of_speech = meaning['partOfSpeech']
                        definitions += f'({str(part_of_speech)}) ' + \
                            str(num)+'. '+definition['definition'] + '\n'
                        defs.append(f'({str(part_of_speech)}) ' +
                                    str(num)+'. '+definition['definition'] + '\n')
                        num += 1
        global index_count
        index_count = 0

        def create_embed(mode):
            global index_count

            if mode == 'next':
                index_count += 1
            elif mode == 'previous':
                index_count -= 1

            if index_count >= len(defs):
                index_count = -1
            elif index_count < 0:
                index_count = 0

            message = f"Here's what i got on the Word {word} \n\n {defs[index_count]}"
            respond_message = Embed(
                title=word,
                description=message,
                color=discord.Color.blurple()
            )

            return respond_message

        async def callback_next(interaction):
            respond_message = create_embed('next')
            await interaction.response.edit_message(embed=respond_message, view=view)

        async def callback_previous(interaction):
            respond_message = create_embed('previous')
            await interaction.response.edit_message(embed=respond_message, view=view)

        button_next = Button(
            label='Next', style=discord.ButtonStyle.green, emoji='➡')
        button_previous = Button(
            label='Previous', style=discord.ButtonStyle.green, emoji='⬅')
        button_next.callback = callback_next
        button_previous.callback = callback_previous
        view = View()
        view.add_item(button_previous)
        view.add_item(button_next)

        await interaction.response.send_message(embed=create_embed('first'), view=view)

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

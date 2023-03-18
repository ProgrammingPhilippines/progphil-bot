import requests
import discord
from discord.ext.commands import Bot, Cog
from discord.app_commands import Choice, choices, command, describe
from utils.decorators import is_staff 

class defineWord(Cog):
    def __init__ (self, bot: Bot):
        self.bot = bot

    @command(name="define",
             description="Give Dictionary Definition to the Given Word")
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
        
        url = "https://api.dictionaryapi.dev/api/v2/entries/en/"+word
        response=requests.get(url)
        
        if "title" in response.json() and response.json()["title"] == "No Definitions Found":
            respond_message=response.json()['message']
        else:
            output=response.json()[0]
            definition=output['meanings'][0]['definitions'][0]['definition']
            respond_message="Word: "+word+"\nDefinition: "+str(definition)
        await interaction.response.send_message(respond_message)
        

async def setup(bot: Bot):
    await bot.add_cog(defineWord(bot))

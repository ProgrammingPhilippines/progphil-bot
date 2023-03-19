import requests
import discord
from discord.ext.commands import Bot
from discord.app_commands import command, describe
from utils.decorators import is_staff 
from discord.ext.commands import GroupCog


# Global Variable that will define if Command is Turned On or Off.
# In Every Restart, this command is by default Turned On.
command_enabled = True 

class Define(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot

    # The Actual Define Command
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
        global command_enabled
        if not command_enabled:
            await interaction.response.send_message("Sorry, this command is currently disabled.")
            return
        
        url = "https://api.dictionaryapi.dev/api/v2/entries/en/" + word
        response = requests.get(url)
        
        if "title" in response.json() and response.json()["title"] == "No Definitions Found":
            respond_message = response.json()['message']
        else:
            definitions=''
            for words in response.json():
                for meaning in words['meanings']:
                    for definition in meaning['definitions']:
                        definitions += definition['definition'] + '\n'
            
            # output=response.json()[0]
            # definition=output['meanings'][0]['definitions'][0]['definition']
            
            respond_message = f"Here's what i got on the Word {word} \n\n {definitions}"
        await interaction.response.send_message(respond_message)

    # Command to Turn this Command On or Off
    @is_staff()
    @command(name="toggle", description="Turn Define Command On/Off")
    async def defineOnOff(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """
        Turn Define Command On/Off

        :param interaction: Interaction
        """
        global command_enabled

        if command_enabled == True:
            command_enabled = False
            response = "Command is now Disabled"
        else:
            command_enabled = True
            response = "Command is now Enabled"

        await interaction.response.send_message(response)
        

async def setup(bot: Bot):
    await bot.add_cog(Define(bot))

from discord.ext.commands import Bot, Cog
from discord import Interaction
from discord.app_commands import command
from discord import app_commands

class Announcements(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
    # Add announcement commands here
    @command(name="announce", description="Make Single Line Announcements on the Channel it was called on") 
    @app_commands.describe(message="The Announcement Message to send")
    async def announce(self, interactions:Interaction,message: str):
        user=interactions.user # get sender 
        channel=interactions.channel # get the channel the command was called on
        allowed_role=["ADMIN","MOD","HELPER"] # the roles allowed for this command 
        user_roles=[role.name.upper() for role in user.roles] # get the list of roles of the user and make it uppercase
        
        if set(user_roles) & set(allowed_role): # this will run if user's role is allowed
            await interactions.response.send_message(f"Announcement has been made",ephemeral=True) 
            await channel.send(message)
        else:  # this will run if user role isn't allowed
            await interactions.response.send_message(f"You dont have permission to use this Command",ephemeral=True)

async def setup(bot: Bot):
    await bot.add_cog(Announcements(bot))
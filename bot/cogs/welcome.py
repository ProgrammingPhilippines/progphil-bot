from discord import Interaction, Member,  TextStyle, MemberFlags
from discord.app_commands import command
from discord.ui import Modal, TextInput, ChannelSelect, View
from discord.ext.commands import Bot, Cog, GroupCog

from database.settings import Settings
from database.welcome import WelcomeDB

from utils.decorators import is_staff

class Welcomer(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.settings = Settings(self.bot.pool)
        self.db = WelcomeDB(self.bot.pool)

    def __parse(self, message: str, member: Member):
        """
        Formats the message from the database
        """
        message = message.replace("{{user}}", member.mention)
        return message
    
    @Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        """
        An event listener that triggers when a member's information is updated.

        Parameters:
        - before (Member): The member object before the update.
        - after (Member): The member object after the update.
        """
        
        # Get the configured channel from the database
        # NOTE: The targetted channel is set by the configure_welcomer method
        channel_id = await self.settings.get_setting("welcome_channel")
        if channel_id == 0:
            return
        channel = after.guild.get_channel(channel_id)
        if channel is None:
            return
        
        # Extracting flags information from the member objects
        # NOTE: The flags contain the onboarding status of the users
        # Reference:
        # https://discordpy.readthedocs.io/en/stable/api.html?highlight=memberflags#discord.MemberFlags
        member_flags_before: MemberFlags = before.flags
        member_flags_after: MemberFlags = after.flags
        
        # Check before and after state of the user's MemberFlags if they finished onboarding
        if (
            not member_flags_before.completed_onboarding
            and member_flags_after.completed_onboarding
        ):
            result = await self.db.get_message()
            if result is None:
                return
            # Run the message through the parse method to replace special strings
            message = self.__parse(result["message"], after)
            await channel.send(message)

    @is_staff()
    @command(name="configure", description="Configure the welcome message")
    async def configure_welcomer(self,interaction: Interaction):
        # Setup the view with a channel select for the channel where the message is going to be sent
        view = View(timeout=1000)
        channel_select = ChannelSelect(placeholder="Select a channel")
        view.add_item(channel_select)
        # Setup the modal with a text input for the message
        modal = Modal(title="Configure the welcome message")
        message_input = TextInput(placeholder="Set the welcome message", label="Message", required=True,style=TextStyle.long)
        modal.add_item(message_input)
        
        # Save the selected channel into the settings database table as "welcome_channel" then send the modal
        async def send_modal(interaction: Interaction):
            channel_id = channel_select.values[0].id
            await self.settings.set_setting("welcome_channel", channel_id)            
            await interaction.response.send_modal(modal)
        
        # Save the inputted text into the database
        async def set_message(interaction: Interaction):
            await self.db.set_message(input.value)
            await interaction.response.send_message(ephemeral=True, content="Successfully set the message")
        
        # Setup the callbacks
        channel_select.callback = send_modal
        modal.on_submit = set_message
        await interaction.response.send_message(view=view, ephemeral=True)
    


async def setup(bot: Bot):
    await bot.add_cog(Welcomer(bot))

from discord import Interaction, Member, Role, TextChannel, TextStyle
from discord.app_commands import command, describe
from discord.ui import Modal, TextInput
from discord.ext.commands import Bot, Cog, GroupCog

from database.settings import Settings
from database.welcome import WelcomeDB


class Welcomer(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.settings = Settings(self.bot.pool)
        self.db = WelcomeDB(self.bot.pool)

    @Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        channel_id = await self.settings.get_setting("welcome_channel")
        role_id = await self.settings.get_setting("welcome_role")
        channel = after.guild.get_channel(channel_id)
        role = after.guild.get_role(role_id)

        if not role:
            return

        if role in before.roles:
            return

        if role not in after.roles:
            return

        message = await self.db.get_message()

        if message:
            message = message[0]["message"].replace("[mention]", f"<@{after.id}>", 1)
        else:
            message = f"Welcome! {after.mention}"

        await channel.send(message)

    @describe(
        role="Member that gets this role will be welcomed.",
        channel="The channel where members will be welcomed"
    )
    @command(name="setup", description="Set the channel to welcome members in.")
    async def set_channel(
        self,
        interaction: Interaction,
        role: Role,
        channel: TextChannel
    ):
        await self.settings.set_setting("welcome_channel", channel.id)
        await self.settings.set_setting("welcome_role", role.id)
        await interaction.response.send_message("Success.", ephemeral=True)

    @command(name="message", description="Edit the welcome message.")
    async def edit_message(self, interaction: Interaction):
        async def modal_callback(interaction: Interaction):
            await self.db.set_message(text.value)
            await interaction.response.send_message("Success", ephemeral=True)

        modal = Modal(title="Welcome Message")
        modal.on_submit = modal_callback
        text = TextInput(label="Message", style=TextStyle.long, max_length=2000)
        modal.add_item(text)

        await interaction.response.send_modal(modal)
        await modal.wait()


async def setup(bot: Bot):
    await bot.add_cog(Welcomer(bot))

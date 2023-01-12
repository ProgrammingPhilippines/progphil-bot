from discord.ext.commands import Bot, Cog
# from discord.app_commands import command


class Announcements(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
    # Add announcement commands here

    # @command(name=..., description=...)
    #     async def ...(self, interaction: Interaction):
    #         ...


async def setup(bot: Bot):
    await bot.add_cog(Announcements(bot))

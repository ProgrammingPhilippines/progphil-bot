from discord.ext.commands import Bot, Cog


class Announcements(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
    # Add announcement commands here


async def setup(bot: Bot):
    await bot.add_cog(Announcements(bot))

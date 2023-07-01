from discord.ext.commands import Bot, Cog, GroupCog


class PeriodicalReminder(GroupCog):
    def __init__(self, bot: Bot):
        self.bot = bot




async def setup(bot):
    await bot.add_cog(PeriodicalReminder(bot))

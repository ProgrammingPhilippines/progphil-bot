from discord.ext.commands import Bot, Cog, Context


class Announcements(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    # Add announcement commands here
    async def announce_with_media(self, ctx: Context):
        pass


def setup(bot: Bot):
    bot.add_cog(Announcements(bot))

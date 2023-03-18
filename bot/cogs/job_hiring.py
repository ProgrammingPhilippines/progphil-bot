
import requests
import discord
from discord import Embed
from discord.ext import tasks
from discord.ext.commands import Bot, GroupCog


class JobHiring(GroupCog):
    ...


def setup(bot: Bot):
    bot.add_cog(JobHiring(bot))

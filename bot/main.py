import os

from discord import Intents
from discord.ext.commands import Bot
from dotenv import load_dotenv


load_dotenv('.env')  # Loads .env file
token = os.getenv('token')
intents = Intents().all()
intents.dm_messages = False


class ProgPhil(Bot):
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            command_prefix="?",
            intents=intents
            )
    
    async def on_ready(self) -> None:
        """Invoked when the bot finish setting up
        
        This can get invoked multiple times, use :meth:`setup_hook()` instead
        for loading databases, etc."""

        print(f'{self.user.display_name} running.')

    async def setup_hook(self) -> None:
        """This method only gets called ONCE, load stuff here."""
        # Load every cog inside cogs folder.
        for cog in os.listdir("bot/cogs"):
            if cog[-3:] == ".py":
                await self.load_extension(f'cogs.{cog[:-3]}')
        await self.tree.sync()


bot = ProgPhil()
bot.run(token)

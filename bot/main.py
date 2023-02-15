import os
import warnings

from aiomysql import Pool, create_pool
from discord import Intents
from discord.ext.commands import Bot

from config import BotConfig, Database


intents = Intents().all()
intents.dm_messages = False  # pycharm showing a warning Intents' object attribute 'dm_messages' is read-only

warnings.filterwarnings("ignore", module="aiomysql")  # surpress annoying aiomysql warnings


class ProgPhil(Bot):
    pool: Pool

    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            command_prefix=BotConfig.prefix,
            intents=intents
        )

    async def on_ready(self) -> None:
        """Invoked when the bot finish setting up

        This can get invoked multiple times, use :meth:`setup_hook()` instead
        for loading databases, etc.
        """

        print(f"{self.user.display_name} running.")

    async def setup_hook(self) -> None:
        """This method only gets called ONCE, load stuff here."""

        # Create a database pool
        self.pool = await create_pool(
            host=Database.host,
            port=3306,
            db=Database.name,
            user=Database.user,
            password=Database.password
        )

        # Load every cog inside cogs folder
        for cog in os.listdir("bot/cogs"):
            if cog[-3:] == ".py":
                await self.load_extension(f"cogs.{cog[:-3]}")

        await self.tree.sync()

    async def close(self):
        await super().close()
        await self.pool.close()


if __name__ == '__main__':
    bot = ProgPhil()
    bot.run(BotConfig.token)

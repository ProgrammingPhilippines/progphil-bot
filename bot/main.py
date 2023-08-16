import os

from asyncpg import Pool, create_pool
from discord import Intents
from discord.ext.commands import Bot
from yoyo import read_migrations, get_backend

from config import BotConfig, Database


intents = Intents().all()
intents.dm_messages = False  # pycharm showing a warning Intents' object attribute 'dm_messages' is read-only


class ProgPhil(Bot):

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

        db_host = Database.host
        db_name = Database.name
        db_user = Database.user
        db_pw = Database.password

        # Create a database pool
        db_port = 21317
        self.pool: Pool = await create_pool(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_pw
        )
        url = f"postgres://avnadmin:AVNS_KP1CwsH4X3Eqv0kjBup@pg-2f0dde7a-cadornajansen4757-9a0b.aivencloud.com:21317/defaultdb?sslmode=require"
        backend = get_backend(url)
        migrations = read_migrations('./migrations')
        backend.apply_migrations(backend.to_apply(migrations))

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

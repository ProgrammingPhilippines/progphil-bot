import os

from src.utils.logging.logger import BotLogger
from src.bot.config import Database, Config, get_config
from src.utils.logging.discord_handler import DiscordHandler

from logging import Logger, StreamHandler
from discord.ext.commands import Bot
import asyncio

from asyncpg import Pool, create_pool
from discord import Intents
from yoyo import read_migrations, get_backend


intents = Intents().all()
intents.dm_messages = False  # pycharm showing a warning Intents' object attribute 'dm_messages' is read-only


class ProgPhil(Bot):
    config: Config
    logger: Logger
    bot_logger: BotLogger
    pool: Pool

    def __init__(self, pool: Pool, cfg: Config, bot_logger: BotLogger, **kwargs):
        bot_cfg = cfg.bot
        super().__init__(
            **kwargs,
            command_prefix=bot_cfg.prefix,
            intents=intents,
        )
        self.bot_logger = bot_logger
        self.logger = self.bot_logger.get_logger()
        self.config = cfg
        self.pool = pool

    async def on_ready(self) -> None:
        """Invoked when the bot finish setting up

        This can get invoked multiple times, use :meth:`setup_hook()` instead
        for loading databases, etc.
        """
        bot_logger = self.bot_logger
        logger_config = self.config.logger
        log_channel = self.get_channel(logger_config.log_channel)

        discord_handler = DiscordHandler(log_channel)
        bot_logger.add_handler(discord_handler)

        logger = bot_logger.get_logger()
        logger.info(f"{self.user.display_name} running.")

        self.logger = logger

    async def setup_hook(self) -> None:
        """This method only gets called ONCE, load stuff here."""

        # Load every cog inside cogs folder
        admin_cogs = get_dir_content("./src/cogs/admin")
        forum_cogs = get_dir_content("./src/cogs/forum")
        fun_cogs = get_dir_content("./src/cogs/fun")
        general_cogs = get_dir_content("./src/cogs/general")
        utility_cogs = get_dir_content("./src/cogs/utility")

        await self.load_cogs("admin", admin_cogs)
        await self.load_cogs("forum", forum_cogs)
        await self.load_cogs("fun", fun_cogs)
        await self.load_cogs("general", general_cogs)
        await self.load_cogs("utility", utility_cogs)

        await self.tree.sync()

    async def load_cogs(self, module: str, cogs: list[str]) -> None:
        """Load cog files as extension to the bot.
        :param module: must match the directory name under cogs/
        :param cogs: list of cogs to load, basically the files under the cogs/<category> that ends with .py
        """
        for cog in cogs:
            if cog.startswith("__init__"):
                continue
            if cog.endswith(".py"):
                await self.load_extension(f"src.cogs.{module}.{cog[:-3]}")

    async def close(self):
        await super().close()
        await self.pool.close()

    async def launch(self):
        """ProgPhil instance starter.
        Use .start to avoid blocking the event loop, so we can use async on main
        """
        await self.start(self.config.bot.token, reconnect=True)


def get_dir_content(path: str) -> list[str]:
    """This returns all the contents(files or directories) from the specified path.
    :param path: path to directory
    """
    return os.listdir(path)


def migrate_db(db: Database, logger: Logger) -> None:
    """
    Will loop through migrations/ folder and attempt to run migration to the database.
    :param db: database config
    """
    url = f"postgresql://{db.user}:{db.password}@{db.host}:{db.port or 5432}/{db.name}"
    logger.info(f"Starting database migration with URL: {url}")

    try:
        backend = get_backend(url)
        migrations = read_migrations("./migrations/")

        with backend.lock():
            to_apply = backend.to_apply(migrations)
            logger.info(f"Found {len(to_apply)} migrations to apply")
            backend.apply_migrations(to_apply)
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")


async def main():
    config = get_config("config/dev-config-void.yml")
    logger_config = config.logger
    logger = BotLogger(logger_config)
    logger.add_handler(StreamHandler())

    db_config = config.database
    dsn = "postgresql://{user}:{password}@{host}:{port}/{database}".format(
        user=db_config.user,
        password=db_config.password,
        host=db_config.host,
        port=db_config.port,
        database=db_config.name,
    )
    pool = await create_pool(dsn)

    migrate_db(db_config, logger.get_logger())

    bot = ProgPhil(pool, config, logger)
    await bot.launch()


def run():
    # run main function forever
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot exiting...")

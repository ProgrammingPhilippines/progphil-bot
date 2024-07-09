import os

from src.utils.logging.discord_handler import init
from src.utils.logging.logger import BotLogger
from logging import Logger

from asyncpg import Pool, create_pool
from discord import Intents
from yoyo import read_migrations, get_backend

from src.bot.config import Database, Config
from src.interface.progphil import IProgPhilBot

intents = Intents().all()
intents.dm_messages = False  # pycharm showing a warning Intents' object attribute 'dm_messages' is read-only


class ProgPhil(IProgPhilBot):
    config: Config
    logger: Logger
    pool: Pool

    def __init__(self, cfg: Config, bot_logger: BotLogger, **kwargs):
        bot_cfg = cfg.bot()
        super().__init__(
            **kwargs,
            command_prefix=bot_cfg.prefix,
            intents=intents,
        )
        self.logger = bot_logger.get_logger(__file__)
        self.config = cfg

    async def on_ready(self) -> None:
        """Invoked when the bot finish setting up

        This can get invoked multiple times, use :meth:`setup_hook()` instead
        for loading databases, etc.
        """

        init(self)
        self.logger.info(f"{self.user.display_name} running.")

    async def setup_hook(self) -> None:
        """This method only gets called ONCE, load stuff here."""
        db_cfg = self.config.database()

        pool = await create_pool(host=db_cfg.host, database=db_cfg.name, user=db_cfg.user,
                               password=db_cfg.password, port=db_cfg.port)
        self.pool = pool

        # Load every cog inside cogs folder
        admin_cogs = get_dir_content("../cogs/admin")
        forum_cogs = get_dir_content("../cogs/forum")
        fun_cogs = get_dir_content("../cogs/fun")
        general_cogs = get_dir_content("../cogs/general")
        utility_cogs = get_dir_content("../cogs/utility")

        await self.load_cogs("admin", admin_cogs)
        await self.load_cogs("forum", forum_cogs)
        await self.load_cogs("fun", fun_cogs)
        await self.load_cogs("general", general_cogs)
        await self.load_cogs("utility", utility_cogs)

        await self.tree.sync()

    async def load_cogs(self, module: str, cogs: list[str]) -> None:
        """
        :param module: must match the directory name under cogs/
        :param cogs: list of cogs to load, basically the files under the cogs/<category> that ends with .py
        """
        for cog in cogs:
            if cog.endswith(".py"):
                await self.load_extension(f"src.cogs.{module}.{cog[:-3]}")

    async def close(self):
        await super().close()
        await self.pool.close()

    def launch(self):
        self.run(self.config.bot().token)


def get_dir_content(path: str) -> list[str]:
    return os.listdir(path)


def migrate_db(db: Database) -> None:
    url = f"postgresql://{db.user}:{db.password}@{db.host}:{db.port or 5432}/{db.name}"
    backend = get_backend(url)
    migrations = read_migrations("../../migrations")
    backend.apply_migrations(backend.to_apply(migrations))


def main():
    config = Config()
    db_config = config.database()
    logger_config = config.logger()

    logger = BotLogger(logger_config)

    migrate_db(db_config)

    bot = ProgPhil(config, logger)
    bot.launch()


if __name__ == "__main__":
    main()

from discord.ext.commands import Bot
from src.bot.config import Config
from asyncpg import Pool

# to avoid cyclic dependency we need to create another class that act as interface for other module to import
# instead of importing ProgPhil from src.bot.main
class IProgPhilBot(Bot):
    config: Config
    pool: Pool

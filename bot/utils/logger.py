import logging.config
from logging import Handler, LogRecord
from discord import TextChannel
from discord.ext.commands import Bot
import asyncio
from config import GuildInfo


class DiscordLoggingHandler(Handler):
    """
    Custom logging handler to send logs to a Discord text channel asynchronously.

    Args:
        messageChannel (TextChannel): The Discord text channel where logs will be sent.

    Custom Attributes:
        __logChannel (TextChannel): The Discord text channel where logs will be sent.
    """

    def __init__(self, messageChannel: TextChannel):
        super().__init__(level=logging.INFO)
        self.__logChannel = messageChannel

    def emit(self, record: LogRecord) -> None:
        asyncio.create_task(self.async_emit(record))

    async def async_emit(self, record: LogRecord):
        log = self.format(record)
        await self.__logChannel.send(log)


def setup_logger(bot: Bot):
    """
    Sets up logging configuration for the bot, including output to stdout and a Discord text channel.

    This function should only be called within the bot's `on_ready` function.

    Args:
        bot (Bot): The Discord bot instance.

    """
    config = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "simple": {
                "format": "[%(asctime)s] %(pathname)s %(levelname)s:\n%(message)s\n"
            }
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "level": logging.DEBUG,
                "stream": "ext://sys.stdout"
            },
        },
        "loggers": {
            "root": {
                "level": logging.INFO,
                "handlers": ["stdout"]
            },
            "console": {
                "level": logging.INFO,
                "handlers": ["stdout"]
            },
        }
    }

    # Checks if the discord logging channel is declared and is a text channel
    channel = bot.get_channel(GuildInfo.log_channel)
    if isinstance(channel, TextChannel) or channel is not None:
        config["handlers"]["discord"] = {
            "()": "utils.logger.DiscordLoggingHandler",
            "messageChannel": (channel),
            "level": logging.DEBUG,
            "formatter": "markdown",
        }
        config["formatters"]["markdown"] = {
            "format": "[%(asctime)s] %(pathname)s **%(levelname)s**\n%(message)s"
        }
        config["loggers"]["discord"] = {
            "level": logging.INFO,
            "handlers": ["discord"]
        }
        config["loggers"]["root"]["handlers"].append("discord")
    logging.config.dictConfig(config=config)
    if not isinstance(channel, TextChannel) or channel is None:
        root_logger = logging.getLogger('root')
        root_logger.info(
            "Discord logger is not declared or is using a non text channel. Please place a text channel's ID in the config.yml file")

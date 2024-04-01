import logging.config
from logging import Handler, LogRecord, Logger
from discord import TextChannel
from discord.ext.commands import Bot
import asyncio
from config import GuildInfo
import yaml
import os


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


class CentralLogger:

    @staticmethod
    def __does_logger_exist(logger: str) -> bool:
        return True if logging.getLogger().manager.loggerDict.get(logger) is not None else False

    @staticmethod
    def setup_logger(bot: Bot):
        """
        Sets up logging configuration for the bot, including output to stdout and a Discord text channel.

        This function should only be called within the bot's `on_ready` function.

        Args:
            bot (Bot): The Discord bot instance.

        """
        error = None
        try:
            # Use the user defined logger configurations if it is properly setup
            if not os.path.exists('logger.yml'):
                error = FileNotFoundError(
                    'logger.yml not found during logger setup. Using default configurations instead. See https://github.com/ProgrammingPhilippines/progphil-bot/wiki/Development-Guide for the configuration guide')
                raise error
            with open('logger.yml', 'r') as f:
                config = yaml.safe_load(f.read())
                if config is None:
                    error = ValueError(
                        'logger.yml file is empty. Using default configurations instead. See https://github.com/ProgrammingPhilippines/progphil-bot/wiki/Development-Guide for the configuration guide')
                    raise error
        except:
            # Load config with default configurations
            config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "simple": {
                        "format": "[%(asctime)s] %(pathname)s %(levelname)s: %(message)s"
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
                    "console": {
                        "level": logging.DEBUG,
                        "handlers": ["stdout"]
                    },
                    "all": {
                        "level": logging.DEBUG,
                        "handlers": ["stdout"]
                    }
                }
            }
        channel = bot.get_channel(GuildInfo.log_channel)
        try:
            # This will error if the logger.yml file is present but configured incorrectly
            if isinstance(channel, TextChannel) or channel is not None:
                config["handlers"]["discord"] = {
                    "()": "utils.logger.DiscordLoggingHandler",
                    "messageChannel": (channel),
                    "level": logging.DEBUG,
                    "formatter": "markdown",
                }
                config["formatters"]["markdown"] = {
                    "format": "```[%(asctime)s] %(pathname)s %(levelname)s: %(message)s```"
                }
                config["loggers"]["discord_text_channel"] = {
                    "level": logging.INFO,
                    "handlers": ["discord"]
                }
                config["loggers"]["all"]["handlers"].append(
                    "discord")

                logging.config.dictConfig(config=config)

            else:
                logging.config.dictConfig(config=config)
                all_logger = CentralLogger.get_logger_all()
                all_logger.warning(
                    "Discord logger was not configured in config.yml or is using a non text channel. Please place a text channel's ID in the config.yml file")
        except:
            # If exception happens while configuring the discord logger, logger.yml is probably wrong so use default config instead
            error = ValueError(
                "logger.yml is configured incorrectly. Using default configuration instead. Please see the docs at https://github.com/ProgrammingPhilippines/progphil-bot/wiki/Development-Guide for the configuration guide")
            config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "simple": {
                        "format": "[%(asctime)s] %(pathname)s %(levelname)s: %(message)s"
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
                    "console": {
                        "level": logging.DEBUG,
                        "handlers": ["stdout"]
                    },
                    "all": {
                        "level": logging.DEBUG,
                        "handlers": ["stdout"]
                    }
                }
            }
            logging.config.dictConfig(config=config)
        else:
            logger = CentralLogger.get_logger_all()
            logger.info(
                "Successfully configured logger with user defined configurations.")

        finally:
            if error:
                logger = CentralLogger.get_logger_all()
                logger.warn(error)

    @staticmethod
    def get_logger_all() -> Logger:
        return logging.getLogger('all')

    @staticmethod
    def get_logger_discord() -> Logger:
        # If the discord logger isnt available, return "all" logger
        if (CentralLogger.__does_logger_exist('discord_text_channel')):
            return logging.getLogger('discord_text_channel')
        else:
            return logging.getLogger('all')

    @staticmethod
    def get_logger_console() -> Logger:
        return logging.getLogger('console')

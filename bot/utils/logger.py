import logging.config
from logging import Handler, LogRecord, Logger
from discord import TextChannel
from discord.ext.commands import Bot
import asyncio
from config import GuildInfo
import yaml
import os

from enum import Enum


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


class CentralLoggerStatusMessage(Enum):
    CONFIG_FILE_DOES_NOT_EXIST = "logger.yml not found during logger setup. Using default configurations instead. See https://github.com/ProgrammingPhilippines/progphil-bot/wiki/Development-Guide for the configuration guide"

    CONFIG_FILE_IS_EMPTY = "logger.yml file is empty. Using default configurations instead. See https://github.com/ProgrammingPhilippines/progphil-bot/wiki/Development-Guide for the configuration guide"

    CONFIG_FILE_MISCONFIGURED = "logger.yml is configured incorrectly. Using default configuration instead. Please see the docs at https://github.com/ProgrammingPhilippines/progphil-bot/wiki/Development-Guide for the configuration guide"

    LOGGER_SETUP_SUCCESS = "Logger setup successful"

    DISCORD_SETUP_SUCCESS = "Successfully configured discord text channel for logging"

    DISCORD_SETUP_FAILURE = "Discord logger was not configured in config.yml or is using a non text channel. Please place a text channel's ID in the config.yml file"

    DISCORD_LOGGER_NOT_AVAILABLE = "Tried using discord text channel logger while it wasn't configured properly. See https://github.com/ProgrammingPhilippines/progphil-bot/wiki/Development-Guide for proper configuration directions"


class CentralLogger:
    __default_config = {
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

    @staticmethod
    def setup_logger(bot: Bot):
        """
        Sets up logging configuration for the bot, including output to stdout and a Discord text channel.

        This function should only be called within the bot's `on_ready` function.

        Args:
            bot (Bot): The Discord bot instance.

        """
        error = None

        # Check if logger.yml doesn't exists in project root
        if not os.path.exists('logger.yml'):
            error = FileNotFoundError(
                CentralLoggerStatusMessage.CONFIG_FILE_DOES_NOT_EXIST.value)
            # Load with default config
            config = CentralLogger.__default_config
        else:
            with open('logger.yml', 'r') as f:
                config = yaml.safe_load(f.read())

            # If config is empty
            if config is None:
                error = ValueError(
                    CentralLoggerStatusMessage.CONFIG_FILE_IS_EMPTY.value)
                # Load config with default configurations
                config = CentralLogger.__default_config

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

                CentralLogger.info(
                    CentralLoggerStatusMessage.DISCORD_SETUP_SUCCESS.value, True)

            else:
                # Configure without discord text channel logging extension
                logging.config.dictConfig(config=config)

                CentralLogger.warning(
                    CentralLoggerStatusMessage.DISCORD_SETUP_FAILURE.value)
        except:
            # If exception happens while configuring the discord logger using user specified configurations, logger.yml is probably wrong so use default config instead

            config = CentralLogger.__default_config

            logging.config.dictConfig(config=config)

            CentralLogger.warning(
                CentralLoggerStatusMessage.CONFIG_FILE_MISCONFIGURED.value)
        finally:
            if error:
                CentralLogger.warning(error)
            CentralLogger.info(
                CentralLoggerStatusMessage.LOGGER_SETUP_SUCCESS.value)

    @staticmethod
    def debug(msg: object, log_on_discord: bool = False):
        if log_on_discord:
            if CentralLogger.__get_logger_discord():
                logger = CentralLogger.__get_logger_all()
            else:
                logger = CentralLogger.__get_logger_console()
                logger.warning(
                    CentralLoggerStatusMessage.DISCORD_LOGGER_NOT_AVAILABLE.value)
        else:
            logger = CentralLogger.__get_logger_console()

        logger.debug(msg)

    @staticmethod
    def info(msg: object, log_on_discord: bool = False):
        if log_on_discord:
            if CentralLogger.__get_logger_discord():
                logger = CentralLogger.__get_logger_all()
            else:
                logger = CentralLogger.__get_logger_console()
                logger.warning(
                    CentralLoggerStatusMessage.DISCORD_LOGGER_NOT_AVAILABLE.value)
        else:
            logger = CentralLogger.__get_logger_console()

        logger.info(msg)

    @staticmethod
    def warning(msg: object, log_on_discord: bool = False):
        if log_on_discord:
            if CentralLogger.__get_logger_discord():
                logger = CentralLogger.__get_logger_all()
            else:
                logger = CentralLogger.__get_logger_console()
                logger.warning(
                    CentralLoggerStatusMessage.DISCORD_LOGGER_NOT_AVAILABLE.value)
        else:
            logger = CentralLogger.__get_logger_console()
        logger.warning(msg)

    @staticmethod
    def error(msg: object, log_on_discord: bool = False):
        if log_on_discord:
            if CentralLogger.__get_logger_discord():
                logger = CentralLogger.__get_logger_all()
            else:
                logger = CentralLogger.__get_logger_console()
                logger.warning(
                    CentralLoggerStatusMessage.DISCORD_LOGGER_NOT_AVAILABLE.value)
        else:
            logger = CentralLogger.__get_logger_console()
        logger.error(msg)

    @staticmethod
    def critical(msg: object, log_on_discord: bool = False):
        if log_on_discord:
            if CentralLogger.__get_logger_discord():
                logger = CentralLogger.__get_logger_all()
            else:
                logger = CentralLogger.__get_logger_console()
                logger.warning(
                    CentralLoggerStatusMessage.DISCORD_LOGGER_NOT_AVAILABLE.value)
        else:
            logger = CentralLogger.__get_logger_console()
        logger.critical(msg)

    @staticmethod
    def __does_logger_exist(logger: str) -> bool:
        return True if logging.getLogger().manager.loggerDict.get(logger) is not None else False

    @staticmethod
    def __get_logger_all() -> Logger:
        return logging.getLogger('all')

    @staticmethod
    def __get_logger_discord() -> Logger | None:
        """ Gets the discord logger. If it isn't available, returns None """
        if (CentralLogger.__does_logger_exist('discord_text_channel')):
            return logging.getLogger('discord_text_channel')
        return

    @staticmethod
    def __get_logger_console() -> Logger:
        return logging.getLogger('console')

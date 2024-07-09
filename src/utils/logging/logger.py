import logging.config

from logging import Formatter, StreamHandler, Handler, Logger
from src.bot.config import LoggerConfig
from src.utils.logging.discord_handler import DiscordHandler

# logging.basicConfig(level=logging.getLevelName(LoggerConfig.log_level))

# [2024-03-19 21:35:00] [INFO] [filepath.py] Sample log XYZ 
_formatter = Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')


class BotLogger(object):
    _stream_handler: Handler
    _discord_handler: Handler

    def __init__(self, logger_config: LoggerConfig):
        logging.basicConfig(level=logging.getLevelName(logger_config.log_level))
        self._stream_handler = StreamHandler()
        self._discord_handler = DiscordHandler()

        self._stream_handler.setFormatter(_formatter)
        self._discord_handler.setFormatter(_formatter)

        self.logger_config = logger_config

    def get_logger(self, name: str) -> Logger:
        logger = logging.getLogger(name)

        logger.addHandler(self._stream_handler)
        logger.addHandler(self._discord_handler)

        return logger

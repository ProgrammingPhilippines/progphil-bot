import logging.config

from logging import Formatter, Handler, Logger
from src.bot.config import LoggerConfig

# logging.basicConfig(level=logging.getLevelName(LoggerConfig.log_level))

# [2024-03-19 21:35:00] [INFO] [filepath.py] Sample log XYZ 
_formatter = Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')


class BotLogger(object):
    _stream_handler: Handler
    _discord_handler: Handler
    logger: Logger

    def __init__(self, logger_config: LoggerConfig):
        self.logger = logging.getLogger(__file__)
        logging.basicConfig(level=logging.getLevelName(logger_config.log_level))

        self.logger_config = logger_config

    def add_handler(self, handler: Handler):
        handler.setFormatter(_formatter)
        self.logger.addHandler(handler)

    def get_logger(self) -> Logger:
        return self.logger

import logging.config
import discord_handler

from logging import Formatter, StreamHandler
from config import LoggerConfig


_discord_handler=discord_handler.DiscordHandler()
logging.basicConfig(level=logging.getLevelName(LoggerConfig.log_level))

# [2024-03-19 21:35:00] [INFO] [filepath.py] Sample log XYZ 
_formatter = Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
_stream_handler = StreamHandler()
_stream_handler.setFormatter(_formatter)
_discord_handler.setFormatter(_formatter)


def getLogger(name):
    logger = logging.getLogger(name)

    logger.addHandler(_stream_handler)
    logger.addHandler(_discord_handler)
    
    return logger

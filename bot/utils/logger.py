import logging.config
from logging import Handler, LogRecord
from discord import TextChannel
from discord.ext.commands import Bot
import asyncio

class DiscordLoggingHandler(Handler):
	def __init__(self, messageChannel: TextChannel):
		super().__init__(level=logging.INFO)
		self.__logChannel = messageChannel
	
	def emit(self, record: LogRecord) -> None:
		asyncio.create_task(self.async_emit(record))
		
	async def async_emit(self, record: LogRecord): 
		log = self.format(record)
		await self.__logChannel.send(log)
     
	

def setup_logger(bot: Bot):
    channel = bot.get_channel(1174194890620543020)
    if not isinstance(channel, TextChannel):
        raise ValueError(channel)
        
    config = {
		"version": 1,
		"disable_existing_loggers": False,
		"formatters": {
			"simple": {
				"format": "%(asctime)s %(pathname)s %(levelname)s: %(message)s"
			}
		},
		"handlers": {
			"stdout": {
				"class": "logging.StreamHandler",
				"formatter": "simple",
    			"level": logging.DEBUG,
    			"stream": "ext://sys.stdout"
			},
			"discord": {
				"()": "utils.logger.DiscordLoggingHandler",
				"messageChannel": (channel),
				"level": logging.INFO,
				"formatter": "simple",
			},
		},
		"loggers": {
			"root": {
				"level": "DEBUG",
				"handlers": ["stdout", "discord"]
			}
		}
	}
    logging.config.dictConfig(config=config)

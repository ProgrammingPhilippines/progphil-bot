from logging import Handler, LogRecord, NOTSET
from discord.ext.commands import Bot
from config import LoggerConfig

import asyncio


_logChannel=None

def init(bot: Bot):
    global _logChannel
    _logChannel = bot.get_channel(LoggerConfig.log_channel)

class DiscordHandler(Handler):
    
    def __init__(self):
        super().__init__(level=NOTSET)
        print(f'Initializing DiscordHandler for channel {_logChannel}')

    def emit(self, record: LogRecord) -> None:
        asyncio.create_task(self.async_emit(record))

    async def async_emit(self, record: LogRecord):
        log = self.format(record)
        await _logChannel.send(log)

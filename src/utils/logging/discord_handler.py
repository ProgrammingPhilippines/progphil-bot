from logging import Handler, LogRecord, NOTSET
from discord.abc import GuildChannel

import asyncio


class DiscordHandler(Handler):
    log_channel: GuildChannel | None

    def __init__(self, log_channel: GuildChannel | None = None):
        super().__init__(level=NOTSET)
        print(f'Initializing DiscordHandler for channel {log_channel}')
        self.log_channel = log_channel

    def emit(self, record: LogRecord) -> None:
        asyncio.create_task(self.async_emit(record))

    async def async_emit(self, record: LogRecord):
        log = self.format(record)
        await self.log_channel.send(f'```{log}```')

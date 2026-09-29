import asyncio
from datetime import datetime, timezone
import re
from typing import TYPE_CHECKING

import discord
from discord import (
    AllowedMentions, Interaction, Message, TextChannel, Thread, app_commands,
)
from discord.app_commands import command, describe
from discord.ext.commands import GroupCog

from src.ai.agent import AIDeps
from src.data.ai.config import AIConfigDB
from src.data.ai.history import AIHistoryDB

if TYPE_CHECKING:
    from src.bot.main import ProgPhil


class AIConfigCog(GroupCog, name="pph-ai"):
    def __init__(self, bot: "ProgPhil") -> None:
        self.bot = bot
        self.db = AIConfigDB(bot.pool)
        self.history_db = AIHistoryDB(bot.pool)
        self._ai_locks: dict[tuple[int, int], asyncio.Lock] = {}

    @GroupCog.listener()
    async def on_message(self, message: Message) -> None:
        if message.author == self.bot.user or message.author.bot:
            return

        guild = message.guild
        if guild is None:
            return

        try:
            mentioned = (
                self.bot.user is not None and self.bot.user.mentioned_in(message)
            )
            content = (
                _clean_bot_mention(message.content, self.bot.user.id)
                if mentioned
                else message.content
            )

            await self._archive_message(message, content=content)

            if mentioned and await self.db.is_enabled_for_channel(
                guild.id, message.channel.id
            ):
                await self._respond_with_ai(message, content)
        except asyncio.TimeoutError:
            self.bot.logger.warning(
                "AI response timed out for message %s", message.id
            )
            await self._send_ai_error(
                message, "I took too long to respond. Please try again."
            )
        except Exception:
            self.bot.logger.exception(
                "AI message handling failed for message %s", message.id
            )
            if (
                self.bot.user is not None
                and self.bot.user.mentioned_in(message)
            ):
                await self._send_ai_error(
                    message, "I couldn't process that right now."
                )

    @GroupCog.listener()
    async def on_message_edit(self, before: Message, after: Message) -> None:
        if after.author.bot or after.guild is None:
            return

        try:
            await self._archive_message(
                after,
                edited_at=after.edited_at or datetime.now(timezone.utc),
            )
        except Exception:
            self.bot.logger.exception(
                "Failed to archive edited message %s", after.id
            )

    @GroupCog.listener()
    async def on_message_delete(self, message: Message) -> None:
        if message.author.bot or message.guild is None:
            return

        try:
            await self._archive_message(
                message,
                deleted_at=datetime.now(timezone.utc),
            )
        except Exception:
            self.bot.logger.exception(
                "Failed to archive deleted message %s", message.id
            )

    async def _send_ai_reply(
        self, message: Message, response: str
    ) -> list[Message]:
        chunks = _split_discord_message(response)
        allowed_mentions = AllowedMentions.none()
        sent_messages = [
            await message.reply(
                chunks[0],
                mention_author=False,
                allowed_mentions=allowed_mentions,
            )
        ]

        for chunk in chunks[1:]:
            sent_messages.append(
                await message.channel.send(
                    chunk,
                    allowed_mentions=allowed_mentions,
                )
            )

        return sent_messages

    async def _respond_with_ai(self, message: Message, content: str) -> None:
        guild = message.guild
        if guild is None:
            return

        lock_key = (guild.id, message.channel.id)
        lock = self._ai_locks.setdefault(lock_key, asyncio.Lock())
        async with lock:
            async with message.channel.typing():
                recent_history = await self.history_db.load_recent_history(
                    guild.id,
                    message.channel.id,
                    exclude_message_id=message.id,
                    before_created_at=message.created_at,
                )
                prompt = content.strip() or "Hello."
                response = await asyncio.wait_for(
                    self.bot.ai.call(
                        prompt,
                        recent_history,
                        AIDeps(
                            history_db=self.history_db,
                            guild_id=guild.id,
                            channel_id=message.channel.id,
                            searchable_channel_ids=(
                                _searchable_channel_ids(message)
                            ),
                        ),
                    ),
                    timeout=45,
                )

                sent_messages = await self._send_ai_reply(message, response)
                try:
                    for sent_message in sent_messages:
                        await self._archive_message(sent_message)
                except Exception:
                    self.bot.logger.exception(
                        "Failed to archive AI response for message %s",
                        message.id,
                    )

    async def _send_ai_error(self, message: Message, content: str) -> None:
        try:
            await message.reply(
                content,
                mention_author=False,
                allowed_mentions=AllowedMentions.none(),
            )
        except Exception:
            self.bot.logger.exception(
                "Failed to send AI error response for message %s", message.id
            )

    async def _archive_message(
        self,
        message: Message,
        *,
        content: str | None = None,
        edited_at: datetime | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        if message.guild is None:
            return

        await self.history_db.ingest_history(
            message.id,
            message.guild.id,
            message.channel.id,
            message.author.id,
            message.content if content is None else content,
            author_is_bot=message.author.bot,
            thread_id=(
                message.channel.id
                if isinstance(message.channel, Thread)
                else None
            ),
            reply_to_message_id=(
                message.reference.message_id
                if message.reference is not None
                else None
            ),
            created_at=message.created_at,
            edited_at=edited_at,
            deleted_at=deleted_at,
        )

    async def backfill_history(self, channel: TextChannel | Thread) -> int:
        count = 0

        async for message in channel.history(limit=None, oldest_first=True):
            await self._archive_message(message)
            count += 1

        return count

    @command(name="toggle", description="Enable or disable the AI assistant.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle(self, interaction: Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        enabled = await self.db.toggle(interaction.guild.id)
        status = "ON" if enabled else "OFF"
        await interaction.response.send_message(
            f"AI assistant is now {status}.", ephemeral=True
        )

    @command(
        name="config",
        description="Enable or disable AI responses in a channel.",
    )
    @describe(
        channel="The channel to configure",
        enabled="Whether AI is enabled there",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def config(
        self,
        interaction: Interaction,
        channel: discord.TextChannel,
        enabled: bool,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        await self.db.set_channel(interaction.guild.id, channel.id, enabled)
        status = "enabled" if enabled else "disabled"
        await interaction.response.send_message(
            f"AI responses {status} in {channel.mention}.", ephemeral=True
        )

    @command(
        name="backfill",
        description="Archive visible server messages for AI history.",
    )
    @describe(channel="Optional channel; omit to archive all visible channels")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def backfill(
        self,
        interaction: Interaction,
        channel: discord.TextChannel | None = None,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        channels = [channel] if channel is not None else [
            *interaction.guild.text_channels,
            *interaction.guild.threads,
        ]
        archived = 0
        failed_channels = 0

        for target_channel in channels:
            try:
                archived += await self.backfill_history(target_channel)
            except (discord.Forbidden, discord.HTTPException):
                failed_channels += 1

        suffix = (
            f" {failed_channels} channel(s) could not be read."
            if failed_channels
            else ""
        )
        await interaction.followup.send(
            f"Archived {archived} messages.{suffix}", ephemeral=True
        )


async def setup(bot: "ProgPhil") -> None:
    await bot.add_cog(AIConfigCog(bot))


def _clean_bot_mention(content: str, bot_id: int) -> str:
    return re.sub(rf"<@!?{bot_id}>", "", content).strip()


def _searchable_channel_ids(message: Message) -> tuple[int, ...]:
    if message.guild is None:
        return (message.channel.id,)

    channel_ids = {message.channel.id}
    channels = [
        *message.guild.text_channels,
        *message.guild.threads,
    ]

    for channel in channels:
        permissions = channel.permissions_for(message.author)

        if permissions.view_channel and permissions.read_message_history:
            channel_ids.add(channel.id)

    return tuple(sorted(channel_ids))


def _split_discord_message(content: str) -> list[str]:
    content = content.strip() or "I don't have a response for that yet."
    return [
        content[index:index + 2000]
        for index in range(0, len(content), 2000)
    ]

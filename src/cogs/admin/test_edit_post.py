import unittest
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from discord import Interaction, NotFound

from ui.modals.edit_post import EditPostModal

from src.cogs.admin.edit_post import EditPost


class TestEditPost(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_bot = MagicMock()
        self.mock_bot.pool = MagicMock()
        self.mock_bot.user = MagicMock()
        self.mock_bot.user.id = 123456789
        self.cog = EditPost(self.mock_bot)

    def _make_interaction(self, *, channel_id=999, done=False):
        interaction = AsyncMock(spec=Interaction)
        interaction.response = AsyncMock()
        interaction.response.send_modal = AsyncMock()
        interaction.response.send_message = AsyncMock()
        interaction.response.is_done = MagicMock(return_value=done)
        interaction.channel = AsyncMock()
        interaction.channel_id = channel_id
        interaction.user = MagicMock()
        return interaction

    async def test_edit_post_sends_modal_for_valid_bot_message(self):
        interaction = self._make_interaction()

        mock_message = AsyncMock()
        mock_message.id = 42
        mock_message.content = "original content"
        mock_message.author = MagicMock()
        mock_message.author.id = self.mock_bot.user.id

        interaction.channel.fetch_message = AsyncMock(return_value=mock_message)

        await self.cog.edit_post.callback(
            self.cog,
            interaction=interaction,
            message_id="42",
        )

        interaction.response.send_modal.assert_awaited_once()
        sent_modal = interaction.response.send_modal.call_args[0][0]
        self.assertIsInstance(sent_modal, EditPostModal)
        self.assertEqual(sent_modal.post_id, 42)
        self.assertEqual(sent_modal.channel_id, 999)
        self.assertEqual(sent_modal.message.default, "original content")

    async def test_edit_post_message_not_found(self):
        interaction = self._make_interaction()
        interaction.channel.fetch_message = AsyncMock(
            side_effect=NotFound(MagicMock(), "not found")
        )

        await self.cog.edit_post.callback(
            self.cog,
            interaction=interaction,
            message_id="42",
        )

        interaction.response.send_message.assert_awaited_once_with(
            "Message not found in this channel.", ephemeral=True
        )
        interaction.response.send_modal.assert_not_awaited()

    async def test_edit_post_invalid_message_id(self):
        interaction = self._make_interaction()

        await self.cog.edit_post.callback(
            self.cog,
            interaction=interaction,
            message_id="not-an-int",
        )

        interaction.response.send_message.assert_awaited_once_with(
            "Message not found in this channel.", ephemeral=True
        )
        interaction.response.send_modal.assert_not_awaited()

    async def test_edit_post_refuses_non_bot_message(self):
        interaction = self._make_interaction()

        mock_message = AsyncMock()
        mock_message.id = 42
        mock_message.content = "someone else's post"
        mock_message.author = MagicMock()
        mock_message.author.id = 999999999  # not the bot

        interaction.channel.fetch_message = AsyncMock(return_value=mock_message)

        await self.cog.edit_post.callback(
            self.cog,
            interaction=interaction,
            message_id="42",
        )

        interaction.response.send_message.assert_awaited_once_with(
            "Cannot edit message that isn't from PPH bot!", ephemeral=True
        )
        interaction.response.send_modal.assert_not_awaited()

    async def test_edit_post_returns_early_when_no_channel_id(self):
        interaction = self._make_interaction(channel_id=None)

        await self.cog.edit_post.callback(
            self.cog,
            interaction=interaction,
            message_id="42",
        )

        interaction.response.send_message.assert_not_awaited()
        interaction.response.send_modal.assert_not_awaited()

    async def test_edit_post_refuses_non_bot_message_when_bot_user_is_none(self):
        self.mock_bot.user = None
        interaction = self._make_interaction()

        mock_message = AsyncMock()
        mock_message.id = 42
        mock_message.content = "some content"
        mock_message.author = MagicMock()
        mock_message.author.id = 999999999

        interaction.channel.fetch_message = AsyncMock(return_value=mock_message)

        await self.cog.edit_post.callback(
            self.cog,
            interaction=interaction,
            message_id="42",
        )

        # bot.user is None, so the author check is skipped, modal should open
        interaction.response.send_modal.assert_awaited_once()


class TestEditPostModal(IsolatedAsyncioTestCase):
    async def test_modal_default_content_is_set(self):
        modal = EditPostModal(
            channel_id=999,
            post_id=42,
            original_content="edit me",
            bot=MagicMock(),
        )

        self.assertEqual(modal.message.default, "edit me")
        self.assertEqual(modal.post_id, 42)
        self.assertEqual(modal.channel_id, 999)

    async def test_on_submit_fetches_and_edits_message(self):
        mock_bot = MagicMock()
        mock_channel = AsyncMock()
        mock_message = AsyncMock()

        mock_bot.fetch_channel = AsyncMock(return_value=mock_channel)
        mock_channel.fetch_message = AsyncMock(return_value=mock_message)
        mock_message.edit = AsyncMock()

        mock_interaction = AsyncMock(spec=Interaction)
        mock_interaction.response = AsyncMock()
        mock_interaction.response.send_message = AsyncMock()

        modal = EditPostModal(
            channel_id=999,
            post_id=42,
            original_content="old content",
            bot=mock_bot,
        )
        modal.message = MagicMock()
        modal.message.value = "new content"

        await modal.on_submit(mock_interaction)

        mock_bot.fetch_channel.assert_awaited_once_with(999)
        mock_channel.fetch_message.assert_awaited_once_with(42)
        mock_message.edit.assert_awaited_once_with(content="new content")
        mock_interaction.response.send_message.assert_awaited_once_with(
            "Success", ephemeral=True
        )


if __name__ == "__main__":
    unittest.main()

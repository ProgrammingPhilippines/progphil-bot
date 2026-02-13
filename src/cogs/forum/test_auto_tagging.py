import unittest
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from discord import Thread, Forbidden, HTTPException
from src.cogs.forum.auto_tagging import AutoTagging


class TestAutoTagging(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_bot = MagicMock()
        self.cog = AutoTagging(self.mock_bot)
        self.mock_db = AsyncMock()
        self.mock_config = AsyncMock()
        self.mock_dev_help_tag_db = AsyncMock()
        self.mock_dev_help_views_db = AsyncMock()
        
        self.cog.db = self.mock_db
        self.cog.config = self.mock_config
        self.cog.dev_help_tag_db = self.mock_dev_help_tag_db
        self.cog.dev_help_views_db = self.mock_dev_help_views_db

    async def test_on_thread_create(self):
        """Test thread creation event handling"""
        mock_thread = MagicMock(spec=Thread)
        mock_thread.id = 123456
        mock_thread.parent.id = 789012
        mock_thread.owner.id = 111222
        
        # Mock the private methods
        self.cog._send_mark_ask_solved_button = AsyncMock()
        self.cog._notify_subscribers = AsyncMock()
        
        await self.cog.on_thread_create(mock_thread)
        
        self.cog._send_mark_ask_solved_button.assert_awaited_once_with(mock_thread)
        self.cog._notify_subscribers.assert_awaited_once_with(mock_thread)

    async def test_send_mark_ask_solved_button_success(self):
        """Test sending mark as solved button successfully"""
        mock_thread = MagicMock(spec=Thread)
        mock_thread.id = 123456
        mock_thread.owner.id = 111222
        
        # Mock thread message
        mock_thread_message = AsyncMock()
        mock_thread_message.thread = mock_thread
        mock_thread.get_partial_message.return_value = mock_thread_message
        
        # Mock bot message
        mock_bot_message = AsyncMock()
        mock_bot_message.id = 333444
        mock_thread.send.return_value = mock_bot_message
        
        # Mock database settings
        self.mock_dev_help_tag_db.get.return_value = {"enabled": True}
        
        await self.cog._send_mark_ask_solved_button(mock_thread)
        
        # Verify message was sent and pinned
        mock_thread.send.assert_awaited_once()
        mock_bot_message.pin.assert_awaited_once()
        
        # Verify database entry was added
        self.mock_dev_help_views_db.add_view.assert_awaited_once_with(
            123456, 333444, 111222
        )

    async def test_send_mark_ask_solved_button_disabled(self):
        """Test when mark as solved button is disabled"""
        mock_thread = MagicMock(spec=Thread)
        
        # Mock database settings - disabled
        self.mock_dev_help_tag_db.get.return_value = None
        
        await self.cog._send_mark_ask_solved_button(mock_thread)
        
        # Should not send any message
        mock_thread.send.assert_not_awaited()

    async def test_notify_subscribers_success(self):
        """Test successful subscriber notification"""
        mock_thread = MagicMock(spec=Thread)
        mock_thread.id = 123456
        mock_thread.parent.id = 789012
        mock_thread.owner.mention = "<@111222>"
        
        # Mock thread message
        mock_thread_message = AsyncMock()
        mock_thread_message.thread = mock_thread
        mock_thread.get_partial_message.return_value = mock_thread_message
        
        # Mock config
        self.mock_config.get_config.return_value = {"config_status": True}
        
        # Mock database responses
        self.mock_db.config_by_forum.return_value = {"id": 1}
        self.mock_db.get_reply.return_value = "Hello {{author}}!"
        self.mock_db.get_tags.return_value = [{"id": 555666, "type": "role"}]
        self.mock_db.get_tag_message.return_value = "Please check this out!"
        
        # Mock guild objects
        mock_role = MagicMock()
        mock_role.mention = "<@&555666>"
        mock_thread.guild.get_role.return_value = mock_role
        
        await self.cog._notify_subscribers(mock_thread)
        
        # Verify thread message was pinned
        mock_thread_message.pin.assert_awaited_once()
        
        # Verify reply was sent (should be called twice - once for reply, once for tags)
        self.assertEqual(mock_thread.send.await_count, 2)
        
        # Check the reply message contains the author mention
        first_call = mock_thread.send.await_args_list[0]
        self.assertIn("<@111222>", first_call[0][0])

    async def test_notify_subscribers_disabled(self):
        """Test when auto tagging is disabled"""
        mock_thread = MagicMock(spec=Thread)
        
        # Mock config as disabled
        self.mock_config.get_config.return_value = {"config_status": False}
        
        await self.cog._notify_subscribers(mock_thread)
        
        # Should not make database calls
        self.mock_db.config_by_forum.assert_not_awaited()

    async def test_notify_subscribers_no_config(self):
        """Test when no configuration exists for the forum"""
        mock_thread = MagicMock(spec=Thread)
        mock_thread.parent.id = 789012
        
        # Mock config as enabled but no forum config
        self.mock_config.get_config.return_value = {"config_status": True}
        self.mock_db.config_by_forum.return_value = None
        
        await self.cog._notify_subscribers(mock_thread)
        
        # Should not proceed to get reply/tags
        self.mock_db.get_reply.assert_not_awaited()

    async def test_notify_subscribers_pin_fails(self):
        """Test when pinning fails but continues with other operations"""
        mock_thread = MagicMock(spec=Thread)
        mock_thread.id = 123456
        mock_thread.parent.id = 789012
        mock_thread.owner.mention = "<@111222>"
        
        # Mock thread message that fails to pin
        mock_thread_message = AsyncMock()
        mock_thread_message.thread = mock_thread
        mock_thread_message.pin.side_effect = [Forbidden(MagicMock(), ""), None, None, None, None]
        mock_thread.get_partial_message.return_value = mock_thread_message
        
        # Mock config and database
        self.mock_config.get_config.return_value = {"config_status": True}
        self.mock_db.config_by_forum.return_value = {"id": 1}
        self.mock_db.get_reply.return_value = "Hello!"
        self.mock_db.get_tags.return_value = []
        self.mock_db.get_tag_message.return_value = None
        
        await self.cog._notify_subscribers(mock_thread)
        
        # Should retry pinning up to 5 times
        self.assertEqual(mock_thread_message.pin.await_count, 5)
        
        # Should still send reply
        mock_thread.send.assert_awaited_once_with("Hello!")

    async def test_view_all_configurations(self):
        """Test viewing all configurations"""
        mock_interaction = AsyncMock()
        mock_interaction.guild = MagicMock()
        
        # Mock database response
        mock_config = {
            "id": 1,
            "forum_id": 789012,
            "reply": "Test reply",
            "created_at": "2023-01-01"
        }
        self.mock_db.list_configurations.return_value = [mock_config]
        
        await self.cog.view_all.callback(self.cog, interaction=mock_interaction)
        
        # Should send response with view
        mock_interaction.response.send_message.assert_awaited_once()
        call_args = mock_interaction.response.send_message.call_args
        self.assertIn('view', call_args.kwargs)
        self.assertTrue(call_args.kwargs['ephemeral'])

    async def test_view_all_no_configurations(self):
        """Test viewing configurations when none exist"""
        mock_interaction = AsyncMock()
        
        # Mock empty database response
        self.mock_db.list_configurations.return_value = []
        
        await self.cog.view_all.callback(self.cog, interaction=mock_interaction)
        
        # Should send "no configurations" message
        mock_interaction.response.send_message.assert_awaited_once_with(
            "There are no configurations.",
            ephemeral=True
        )


if __name__ == "__main__":
    unittest.main()

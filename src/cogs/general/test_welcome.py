import unittest
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta, timezone

from discord import MemberFlags
from src.cogs.general.welcome import Welcomer


class TestWelcome(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_bot = MagicMock()
        self.cog = Welcomer(self.mock_bot)
        self.mock_settings = AsyncMock()
        self.mock_db = AsyncMock()
        self.cog.settings = self.mock_settings
        self.cog.db = self.mock_db

    def test_parse_message(self):
        """Test message parsing with user mention replacement"""
        mock_member = MagicMock()
        mock_member.mention = "<@123456789>"
        
        message = "Welcome {{user}} to our server!"
        result = self.cog._Welcomer__parse(message, mock_member)
        
        expected = "Welcome <@123456789> to our server!"
        self.assertEqual(result, expected)

    def test_parse_message_no_placeholder(self):
        """Test message parsing without placeholder"""
        mock_member = MagicMock()
        mock_member.mention = "<@123456789>"
        
        message = "Welcome to our server!"
        result = self.cog._Welcomer__parse(message, mock_member)
        
        self.assertEqual(result, message)

    async def test_on_member_update_onboarding_completed(self):
        """Test member update when onboarding is completed"""
        # Mock member objects
        mock_before = MagicMock()
        mock_after = MagicMock()
        
        # Mock member flags
        mock_flags_before = MagicMock(spec=MemberFlags)
        mock_flags_before.completed_onboarding = False
        mock_flags_after = MagicMock(spec=MemberFlags)
        mock_flags_after.completed_onboarding = True
        
        mock_before.flags = mock_flags_before
        mock_after.flags = mock_flags_after
        
        # Mock joined_at to be recent (within 1 day)
        recent_time = datetime.now(timezone.utc) - timedelta(hours=12)
        mock_after.joined_at = recent_time
        
        # Mock guild and channel
        mock_channel = AsyncMock()
        mock_guild = MagicMock()
        mock_guild.get_channel.return_value = mock_channel
        mock_after.guild = mock_guild
        
        # Mock settings and database
        self.mock_settings.get_setting.return_value = 123456  # channel_id
        self.mock_db.get_message.return_value = {"message": "Welcome {{user}}!"}
        
        await self.cog.on_member_update(mock_before, mock_after)
        
        # Verify channel was retrieved and message was sent
        mock_guild.get_channel.assert_called_once_with(123456)
        mock_channel.send.assert_awaited_once()
        
        # Check that the message was parsed correctly
        sent_message = mock_channel.send.call_args[0][0]
        self.assertIn(mock_after.mention, sent_message)

    async def test_on_member_update_no_channel_configured(self):
        """Test member update when no welcome channel is configured"""
        mock_before = MagicMock()
        mock_after = MagicMock()
        
        # Mock settings to return 0 (no channel configured)
        self.mock_settings.get_setting.return_value = 0
        
        await self.cog.on_member_update(mock_before, mock_after)
        
        # Should return early, no database calls
        self.mock_db.get_message.assert_not_awaited()

    async def test_on_member_update_channel_not_found(self):
        """Test member update when configured channel doesn't exist"""
        mock_before = MagicMock()
        mock_after = MagicMock()
        
        # Mock guild to return None for channel
        mock_guild = MagicMock()
        mock_guild.get_channel.return_value = None
        mock_after.guild = mock_guild
        
        self.mock_settings.get_setting.return_value = 123456
        
        await self.cog.on_member_update(mock_before, mock_after)
        
        # Should return early, no database calls
        self.mock_db.get_message.assert_not_awaited()

    async def test_on_member_update_already_completed_onboarding(self):
        """Test member update when onboarding was already completed"""
        mock_before = MagicMock()
        mock_after = MagicMock()
        
        # Both before and after have completed onboarding
        mock_flags_before = MagicMock(spec=MemberFlags)
        mock_flags_before.completed_onboarding = True
        mock_flags_after = MagicMock(spec=MemberFlags)
        mock_flags_after.completed_onboarding = True
        
        mock_before.flags = mock_flags_before
        mock_after.flags = mock_flags_after
        
        mock_guild = MagicMock()
        mock_after.guild = mock_guild
        
        self.mock_settings.get_setting.return_value = 123456
        
        await self.cog.on_member_update(mock_before, mock_after)
        
        # Should not send welcome message
        self.mock_db.get_message.assert_not_awaited()

    async def test_on_member_update_joined_too_long_ago(self):
        """Test member update when member joined more than 1 day ago"""
        mock_before = MagicMock()
        mock_after = MagicMock()
        
        # Mock member flags for onboarding completion
        mock_flags_before = MagicMock(spec=MemberFlags)
        mock_flags_before.completed_onboarding = False
        mock_flags_after = MagicMock(spec=MemberFlags)
        mock_flags_after.completed_onboarding = True
        
        mock_before.flags = mock_flags_before
        mock_after.flags = mock_flags_after
        
        # Mock joined_at to be more than 1 day ago
        old_time = datetime.now(timezone.utc) - timedelta(days=2)
        mock_after.joined_at = old_time
        
        mock_guild = MagicMock()
        mock_after.guild = mock_guild
        
        self.mock_settings.get_setting.return_value = 123456
        
        await self.cog.on_member_update(mock_before, mock_after)
        
        # Should not send welcome message
        self.mock_db.get_message.assert_not_awaited()

    async def test_on_member_update_no_welcome_message(self):
        """Test member update when no welcome message is configured"""
        mock_before = MagicMock()
        mock_after = MagicMock()
        
        # Mock member flags
        mock_flags_before = MagicMock(spec=MemberFlags)
        mock_flags_before.completed_onboarding = False
        mock_flags_after = MagicMock(spec=MemberFlags)
        mock_flags_after.completed_onboarding = True
        
        mock_before.flags = mock_flags_before
        mock_after.flags = mock_flags_after
        
        # Mock recent join time
        recent_time = datetime.now(timezone.utc) - timedelta(hours=12)
        mock_after.joined_at = recent_time
        
        # Mock guild and channel
        mock_channel = AsyncMock()
        mock_guild = MagicMock()
        mock_guild.get_channel.return_value = mock_channel
        mock_after.guild = mock_guild
        
        # Mock settings but no message in database
        self.mock_settings.get_setting.return_value = 123456
        self.mock_db.get_message.return_value = None
        
        await self.cog.on_member_update(mock_before, mock_after)
        
        # Should not send any message
        mock_channel.send.assert_not_awaited()

    async def test_configure_welcomer(self):
        """Test configure welcomer command"""
        mock_interaction = AsyncMock()
        
        await self.cog.configure_welcomer.callback(self.cog, interaction=mock_interaction)
        
        # Should send a view with channel select
        mock_interaction.response.send_message.assert_awaited_once()
        call_args = mock_interaction.response.send_message.call_args
        self.assertIn('view', call_args.kwargs)
        self.assertTrue(call_args.kwargs['ephemeral'])


if __name__ == "__main__":
    unittest.main()

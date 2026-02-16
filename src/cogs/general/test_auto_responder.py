import unittest
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock

from src.cogs.general.auto_responder import Responder


class TestAutoResponder(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_bot = MagicMock()
        self.cog = Responder(self.mock_bot)
        self.mock_db = AsyncMock()
        self.cog.db = self.mock_db

    async def test_on_message_strict_match(self):
        """Test on_message with strict matching"""
        # Mock message
        mock_message = MagicMock()
        mock_message.author.bot = False
        mock_message.content = "hello"
        mock_message.channel.id = 123456
        mock_message.reply = AsyncMock()

        # Mock database responses
        self.mock_db.get_responses.return_value = [
            {
                "id": 1,
                "message": "hello",
                "response": "Hello there!",
                "matching_type": "strict",
                "response_type": "reply",
                "specified": False
            }
        ]
        self.mock_db.get_response_channels.return_value = []

        await self.cog.on_message(mock_message)

        mock_message.reply.assert_awaited_once_with("Hello there!")

    async def test_on_message_lenient_match(self):
        """Test on_message with lenient matching"""
        mock_message = MagicMock()
        mock_message.author.bot = False
        mock_message.content = "Hello World"
        mock_message.channel.id = 123456
        mock_message.channel.send = AsyncMock()

        self.mock_db.get_responses.return_value = [
            {
                "id": 1,
                "message": "hello",
                "response": "Hi there!",
                "matching_type": "lenient",
                "response_type": "regular",
                "specified": False
            }
        ]
        self.mock_db.get_response_channels.return_value = []

        await self.cog.on_message(mock_message)

        mock_message.channel.send.assert_awaited_once_with("Hi there!")

    async def test_on_message_bot_ignored(self):
        """Test that bot messages are ignored"""
        mock_message = MagicMock()
        mock_message.author.bot = True

        await self.cog.on_message(mock_message)

        self.mock_db.get_responses.assert_not_awaited()

    async def test_on_message_channel_specific(self):
        """Test channel-specific responses"""
        mock_message = MagicMock()
        mock_message.author.bot = False
        mock_message.content = "test"
        mock_message.channel.id = 123456
        mock_message.channel.send = AsyncMock()

        # Response is specified for certain channels only
        self.mock_db.get_responses.return_value = [
            {
                "id": 1,
                "message": "test",
                "response": "Test response",
                "matching_type": "strict",
                "response_type": "regular",
                "specified": True
            }
        ]
        # Message channel is not in allowed channels
        self.mock_db.get_response_channels.return_value = [789012]

        await self.cog.on_message(mock_message)

        # Should not respond since channel is not allowed
        mock_message.channel.send.assert_not_awaited()

    async def test_on_message_no_match(self):
        """Test when no responses match"""
        mock_message = MagicMock()
        mock_message.author.bot = False
        mock_message.content = "no match"
        mock_message.channel.send = AsyncMock()

        self.mock_db.get_responses.return_value = [
            {
                "id": 1,
                "message": "hello",
                "response": "Hi!",
                "matching_type": "strict",
                "response_type": "regular",
                "specified": False
            }
        ]

        await self.cog.on_message(mock_message)

        mock_message.channel.send.assert_not_awaited()

    def test_match_strict(self):
        """Test strict matching logic"""
        # Test exact match
        result = self.cog._Responder__match("hello", "hello", "strict")
        self.assertTrue(result)

        # Test non-match
        result = self.cog._Responder__match("hello world", "hello", "strict")
        self.assertFalse(result)

    def test_match_lenient(self):
        """Test lenient matching logic"""
        # Test case-insensitive substring match
        result = self.cog._Responder__match("Hello World", "hello", "lenient")
        self.assertTrue(result)

        # Test non-match
        result = self.cog._Responder__match("goodbye", "hello", "lenient")
        self.assertFalse(result)

    def test_match_strict_contains(self):
        """Test strict contains matching logic"""
        # Test word boundary match
        result = self.cog._Responder__match("hello world", "hello", "strict_contains")
        self.assertTrue(result)

        # Test non-word boundary (should not match)
        result = self.cog._Responder__match("helloworld", "hello", "strict_contains")
        self.assertFalse(result)

    def test_match_regex(self):
        """Test regex matching logic"""
        # Test simple regex match
        result = self.cog._Responder__match("hello123", r"hello\d+", "regex")
        self.assertTrue(result)

        # Test non-match
        result = self.cog._Responder__match("hello", r"hello\d+", "regex")
        self.assertFalse(result)

    async def test_view_responses_with_data(self):
        """Test viewing responses when data exists"""
        mock_interaction = AsyncMock()
        
        self.mock_db.get_responses.return_value = [
            {
                "id": 1,
                "message": "hello",
                "response": "Hi there!",
                "response_type": "reply",
                "matching_type": "strict"
            }
        ]
        self.mock_db.records_count.return_value = 1

        await self.cog.view_responses.callback(self.cog, interaction=mock_interaction)

        mock_interaction.response.send_message.assert_awaited_once()
        call_args = mock_interaction.response.send_message.call_args
        self.assertIn('embed', call_args.kwargs)
        self.assertTrue(call_args.kwargs['ephemeral'])

    async def test_view_responses_no_data(self):
        """Test viewing responses when no data exists"""
        mock_interaction = AsyncMock()
        
        self.mock_db.get_responses.return_value = []

        await self.cog.view_responses.callback(self.cog, interaction=mock_interaction)

        mock_interaction.response.send_message.assert_awaited_once()
        call_args = mock_interaction.response.send_message.call_args
        embed = call_args.kwargs['embed']
        self.assertIn("Nothing yet...", embed.description)

    async def test_delete_response_success(self):
        """Test successful response deletion"""
        mock_interaction = AsyncMock()
        
        self.mock_db.records_count.return_value = 1
        self.mock_db.delete_response.return_value = True

        await self.cog.delete_responses.callback(self.cog, interaction=mock_interaction, response_id=1)

        self.mock_db.delete_response.assert_awaited_once_with(1)
        mock_interaction.response.send_message.assert_awaited_once_with(
            "Deleted Successfully.",
            ephemeral=True
        )

    async def test_delete_response_not_found(self):
        """Test deleting non-existent response"""
        mock_interaction = AsyncMock()
        
        self.mock_db.records_count.return_value = 1
        self.mock_db.delete_response.return_value = False

        await self.cog.delete_responses.callback(self.cog, interaction=mock_interaction, response_id=999)

        mock_interaction.response.send_message.assert_awaited_once_with(
            "There was a problem deleting #999. It may not exist.",
            ephemeral=True
        )


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, time

from src.cogs.general.trivia import Trivia


class TestTrivia(IsolatedAsyncioTestCase):
    @patch("src.cogs.general.trivia.requests.get")
    async def test_trivia_loop_success(self, mock_get):
        """Test successful trivia loop execution"""
        mock_bot = MagicMock()
        mock_bot.config.api.api_ninja = "test_api_key"
        
        # Mock channels
        mock_trivia_channel = AsyncMock()
        mock_log_channel = AsyncMock()
        mock_bot.get_channel.side_effect = lambda channel_id: {
            123456: mock_trivia_channel,
            789012: mock_log_channel
        }.get(channel_id)
        mock_bot.config.guild.log_channel = 789012

        # Mock config and database
        mock_config = AsyncMock()
        mock_config.get_config.return_value = {"config_status": True}
        
        mock_db = AsyncMock()
        
        cog = Trivia(mock_bot)
        cog.config = mock_config
        cog.db = mock_db
        cog.sched = {"channel_id": "123456", "schedule": "12:00"}
        cog.sent_today = False
        cog.sent_date = None

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = [{"fact": "Test trivia fact"}]
        mock_get.return_value = mock_response

        # Mock datetime to ensure trivia should be sent
        with patch("src.cogs.general.trivia.datetime") as mock_datetime:
            mock_datetime.today.return_value.date.return_value = datetime(2023, 1, 1).date()
            mock_datetime.utcnow.return_value.time.return_value = time(13, 0)  # After 12:00
            
            await cog.trivia_loop()

        mock_get.assert_called_once_with(
            "https://api.api-ninjas.com/v1/facts",
            headers={"X-Api-Key": "test_api_key"}
        )
        mock_trivia_channel.send.assert_awaited_once()
        
        # Check that sent_today is now True
        self.assertTrue(cog.sent_today)

    @patch("src.cogs.general.trivia.requests.get")
    async def test_trivia_loop_api_error(self, mock_get):
        """Test trivia loop when API returns error"""
        mock_bot = MagicMock()
        mock_bot.config.api.api_ninja = "test_api_key"
        
        mock_trivia_channel = AsyncMock()
        mock_log_channel = AsyncMock()
        mock_bot.get_channel.side_effect = lambda channel_id: {
            123456: mock_trivia_channel,
            789012: mock_log_channel
        }.get(channel_id)
        mock_bot.config.guild.log_channel = 789012

        mock_config = AsyncMock()
        mock_config.get_config.return_value = {"config_status": True}
        
        cog = Trivia(mock_bot)
        cog.config = mock_config
        cog.sched = {"channel_id": "123456", "schedule": "12:00"}
        cog.sent_today = False

        # Mock API error response
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with patch("src.cogs.general.trivia.datetime") as mock_datetime:
            mock_datetime.today.return_value.date.return_value = datetime(2023, 1, 1).date()
            mock_datetime.utcnow.return_value.time.return_value = time(13, 0)
            
            await cog.trivia_loop()

        mock_log_channel.send.assert_awaited_once_with("Trivia API Error: 500")
        mock_trivia_channel.send.assert_not_awaited()

    async def test_trivia_loop_disabled(self):
        """Test trivia loop when feature is disabled"""
        mock_bot = MagicMock()
        mock_config = AsyncMock()
        mock_config.get_config.return_value = {"config_status": False}
        
        cog = Trivia(mock_bot)
        cog.config = mock_config
        cog.sched = {"channel_id": "123456", "schedule": "12:00"}

        with patch("src.cogs.general.trivia.requests.get") as mock_get:
            await cog.trivia_loop()

        mock_get.assert_not_called()

    async def test_trivia_loop_no_schedule(self):
        """Test trivia loop when no schedule is configured"""
        mock_bot = MagicMock()
        cog = Trivia(mock_bot)
        cog.sched = None

        with patch("src.cogs.general.trivia.requests.get") as mock_get:
            await cog.trivia_loop()

        mock_get.assert_not_called()

    async def test_toggle_command(self):
        """Test toggle command"""
        mock_bot = MagicMock()
        mock_interaction = AsyncMock()
        mock_config = AsyncMock()
        mock_config.get_config.return_value = {"config_status": True}
        mock_config.toggle_config.return_value = True

        cog = Trivia(mock_bot)
        cog.config = mock_config

        await cog.toggle.callback(cog, interaction=mock_interaction)

        mock_config.toggle_config.assert_awaited_once_with("trivia")
        mock_interaction.response.send_message.assert_awaited_once_with(
            "Turned ON Trivias.",
            ephemeral=True
        )

    def test_get_schedule(self):
        """Test _get_schedule method"""
        mock_bot = MagicMock()
        cog = Trivia(mock_bot)
        
        # Test with no schedule
        cog.sched = None
        result = cog._get_schedule()
        self.assertEqual(result, time(0, 0))
        
        # Test with schedule
        cog.sched = {"schedule": "14:30"}
        with patch("src.cogs.general.trivia.datetime") as mock_datetime:
            mock_datetime.strptime.return_value.time.return_value = time(14, 30)
            mock_datetime.combine.return_value = datetime(2023, 1, 1, 14, 30)
            mock_datetime.today.return_value = datetime(2023, 1, 1)
            
            result = cog._get_schedule()
            # Should return time adjusted for UTC conversion (14:30 - 8 hours = 6:30)
            self.assertEqual(result, time(6, 30))


if __name__ == "__main__":
    unittest.main()

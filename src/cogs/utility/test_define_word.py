import unittest
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from src.cogs.utility.define_word import Define


class TestDefineWord(IsolatedAsyncioTestCase):
    @patch("src.cogs.utility.define_word.requests.get")
    async def test_define_word_success(self, mock_get):
        """Test successful word definition lookup"""
        mock_config = AsyncMock()
        mock_config.get_config.return_value = {"config_status": True}

        mock_bot = MagicMock()
        mock_ctx = AsyncMock()
        cog = Define(mock_bot)
        cog.config = mock_config

        mock_member = MagicMock()
        mock_member.id = 1234567890
        mock_member.display_name = "Test User"
        mock_ctx.author = mock_member

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = [
            {
                "meanings": [
                    {
                        "partOfSpeech": "noun",
                        "definitions": [
                            {"definition": "A greeting or expression of goodwill"}
                        ]
                    }
                ]
            }
        ]
        mock_get.return_value = mock_response

        expected_url = "https://api.dictionaryapi.dev/api/v2/entries/en/hello"

        await cog.define.callback(cog, ctx=mock_ctx, word="hello")

        mock_get.assert_called_once_with(expected_url)
        mock_ctx.send.assert_awaited_once()
        
        # Check that an embed was sent
        call_args = mock_ctx.send.call_args
        self.assertIn('embed', call_args.kwargs)

    @patch("src.cogs.utility.define_word.requests.get")
    async def test_define_word_not_found(self, mock_get):
        """Test word not found scenario"""
        mock_config = AsyncMock()
        mock_config.get_config.return_value = {"config_status": True}

        mock_bot = MagicMock()
        mock_ctx = AsyncMock()
        cog = Define(mock_bot)
        cog.config = mock_config

        mock_member = MagicMock()
        mock_member.id = 1234567890
        mock_ctx.author = mock_member

        # Mock API response for word not found
        mock_response = MagicMock()
        mock_response.ok = False
        mock_get.return_value = mock_response

        await cog.define.callback(cog, ctx=mock_ctx, word="nonexistentword")

        mock_ctx.send.assert_awaited_once()
        
        # Check that an embed with error message was sent
        call_args = mock_ctx.send.call_args
        self.assertIn('embed', call_args.kwargs)

    @patch("src.cogs.utility.define_word.requests.get")
    async def test_define_word_disabled(self, mock_get):
        """Test when the define word feature is disabled"""
        mock_config = AsyncMock()
        mock_config.get_config.return_value = {"config_status": False}

        mock_bot = MagicMock()
        mock_ctx = AsyncMock()
        cog = Define(mock_bot)
        cog.config = mock_config

        await cog.define.callback(cog, ctx=mock_ctx, word="hello")

        # Should not make API call when disabled
        mock_get.assert_not_called()
        mock_ctx.send.assert_awaited_once_with("Sorry, this command is currently disabled.")

    async def test_toggle_config(self):
        """Test toggling the define word configuration"""
        mock_config = AsyncMock()
        mock_config.toggle_config.return_value = True

        mock_bot = MagicMock()
        mock_interaction = AsyncMock()
        cog = Define(mock_bot)
        cog.config = mock_config

        await cog.toggle_config.callback(cog, interaction=mock_interaction)

        mock_config.toggle_config.assert_awaited_once_with("define_word")
        mock_interaction.response.send_message.assert_awaited_once_with(
            "Turned ON Define Word.",
            ephemeral=True
        )

    def test_format_data(self):
        """Test the static _format_data method"""
        test_data = [
            {
                "meanings": [
                    {
                        "partOfSpeech": "noun",
                        "definitions": [
                            {"definition": "A greeting"},
                            {"definition": "An expression of goodwill"}
                        ]
                    },
                    {
                        "partOfSpeech": "verb",
                        "definitions": [
                            {"definition": "To greet someone"}
                        ]
                    }
                ]
            }
        ]

        result = Define._format_data(test_data)
        
        expected = [
            ("verb", "To greet someone"),
            ("noun", "An expression of goodwill"),
            ("noun", "A greeting")
        ]
        
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()

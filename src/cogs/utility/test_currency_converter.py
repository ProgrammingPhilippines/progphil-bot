import unittest
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, Mock, patch

from asyncpg.connection import os
from src.cogs.utility.currency_converter import Converter

class TestCurrencyConverter(IsolatedAsyncioTestCase):
    @patch("src.cogs.utility.currency_converter.requests.get")
    async def test_currency_converter(self, mock_get):
        mock_config = AsyncMock()

        os.environ["currency_api_key"] = "test_key"

        mock_bot = MagicMock()
        mock_ctx = AsyncMock()
        cog = Converter(mock_bot)
        cog.config = mock_config
        cog.symbols = [
            ("AED", "United Arab Emirates Dirham"),
            ("AFN", "Afghan Afghani"),
            ("ALL", "Albanian Lek"),
            ("AMD", "Armenian Dram"),
            ("USD", "United States Dollar"),
            ("EUR", "Euro"),
        ("GBP", "British Pound Sterling"),
        ]

        mock_member = MagicMock()
        mock_member.id = 1234567890
        mock_member.display_name = "Test User"
        mock_member.name = "Test User"
        mock_ctx.author = mock_member

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "result": 89.0}
        mock_get.return_value = mock_response

        expected_url = "https://api.apilayer.com/currency_data/convert?from=USD&to=EUR&amount=100"

        await cog.config.get_config("currency_converter")
        await cog.exchange.callback(cog, ctx=mock_ctx, amount="100", from_currency="USD", to_currency="EUR")

        mock_get.assert_called_once_with(expected_url, headers={"apiKey": "test_key"})
        mock_ctx.send.assert_awaited_with("The exchange rate for 100.0 USD is around 89.0 EUR.")


if __name__ == "__main__":
    unittest.main()

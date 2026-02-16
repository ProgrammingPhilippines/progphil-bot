import unittest
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from discord import ForumChannel, Thread

from src.cogs.forum.auto_tagging import ForumAssist


class TestForumAssist(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_bot = MagicMock()
        self.mock_bot.pool = MagicMock()
        self.mock_bot.logger = MagicMock()
        self.mock_bot.tree = MagicMock()
        self.mock_bot.config = MagicMock()
        self.mock_bot.config.guild.staff_roles = [1, 2]

        self.cog = ForumAssist(self.mock_bot)
        self.cog.db = AsyncMock()
        self.cog.config = AsyncMock()

    async def test_send_mark_as_solved_button_success(self):
        thread = MagicMock(spec=Thread)
        thread.id = 123
        thread.owner_id = 456
        thread.parent_id = 789
        thread.parent = MagicMock(spec=ForumChannel)
        thread.parent.id = 789

        sent_message = AsyncMock()
        sent_message.id = 999
        thread.send = AsyncMock(return_value=sent_message)

        self.cog.db.is_mark_as_solved_enabled_for_forum.return_value = (1, True)
        self.cog.config.get_config.return_value = {"config_status": True}
        self.cog.db.config_by_forum.return_value = {"id": 1}
        self.cog.db.get_mark_as_solved_tag.return_value = 111

        await self.cog._send_mark_ask_solved_button(thread)

        thread.send.assert_awaited_once()
        sent_message.pin.assert_awaited_once()
        self.cog.db.add_persistent_mark_as_solved_view.assert_awaited_once_with(
            123, 999, 456
        )

    async def test_send_mark_as_solved_button_skips_when_tag_missing(self):
        thread = MagicMock(spec=Thread)
        thread.id = 123
        thread.owner_id = 456
        thread.parent_id = 789
        thread.parent = MagicMock(spec=ForumChannel)
        thread.parent.id = 789
        thread.send = AsyncMock()

        self.cog.db.is_mark_as_solved_enabled_for_forum.return_value = (1, True)
        self.cog.config.get_config.return_value = {"config_status": True}
        self.cog.db.config_by_forum.return_value = {"id": 1}
        self.cog.db.get_mark_as_solved_tag.return_value = None

        await self.cog._send_mark_ask_solved_button(thread)

        thread.send.assert_not_awaited()
        self.cog.db.add_persistent_mark_as_solved_view.assert_not_awaited()

    async def test_send_mark_as_solved_button_skips_when_disabled(self):
        thread = MagicMock(spec=Thread)
        thread.id = 123
        thread.owner_id = 456
        thread.parent_id = 789
        thread.parent = MagicMock(spec=ForumChannel)
        thread.parent.id = 789
        thread.send = AsyncMock()

        self.cog.db.is_mark_as_solved_enabled_for_forum.return_value = (1, False)

        await self.cog._send_mark_ask_solved_button(thread)

        thread.send.assert_not_awaited()
        self.cog.config.get_config.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from discord import Interaction
from discord.app_commands import Choice

from src.cogs.admin.announcements import Announcements
from src.ui.modals.announcement import Announcement, _format_announcement


class TestAnnouncementFormatting(unittest.TestCase):
    def test_format_announcement_with_title_uses_single_newline(self):
        announcement = _format_announcement("my title", "test")

        self.assertEqual(announcement, "**my title**\ntest")

    def test_format_announcement_without_title_has_no_leading_newline(self):
        announcement = _format_announcement("", "test")

        self.assertEqual(announcement, "test")

    def test_format_announcement_with_whitespace_title_treats_it_as_missing(self):
        announcement = _format_announcement("   ", "test")

        self.assertEqual(announcement, "test")


class TestAnnouncements(IsolatedAsyncioTestCase):
    @patch("src.cogs.admin.announcements.Announcement.wait", new_callable=AsyncMock)
    async def test_announce_command(self, mock_wait):
        mock_bot = MagicMock()
        mock_interaction = AsyncMock(specs=Interaction)
        mock_interaction.response = AsyncMock()
        mock_interaction.response.send_modal = AsyncMock()
        mock_interaction.user = MagicMock()
        mock_interaction.user.name = "test_user"

        mock_channel = MagicMock()
        mock_channel.name = "test_channel"
        mock_channel.send = MagicMock()

        mock_photo = MagicMock()
        mock_photo.filename = "image.jpg"
        # mock_photo.filename.value = "image.jpg"

        cog = Announcements(mock_bot)
        mock_logger = MagicMock()
        mock_logger.info = MagicMock()
        cog.logger = mock_logger

        mock_mention = MagicMock()
        mock_mention.mention = "<@1234567890>"
        mock_mention.value = "1234567890"

        mock_submission_type = MagicMock()
        mock_submission_type.value = "regular"

        await cog.announce.callback(cog,interaction=mock_interaction, submission_type=mock_submission_type, channel=mock_channel, photo=mock_photo, mention=mock_mention)

        mock_interaction.response.send_modal.assert_awaited_once()

        cog.logger.info.assert_called_once_with(f"A announcement was made by {mock_interaction.user} in {mock_channel.name}")
        sent_modal = mock_interaction.response.send_modal.call_args[0][0]

        self.assertIsInstance(sent_modal, Announcement)
        mock_wait.assert_awaited_once()

    async def test_on_submit_regular_submission_uses_single_newline(self):
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock()

        mock_interaction = MagicMock(spec=Interaction)
        mock_interaction.response = MagicMock()
        mock_interaction.response.is_done = MagicMock(return_value=False)
        mock_interaction.response.send_message = AsyncMock()
        mock_interaction.followup = MagicMock()
        mock_interaction.followup.send = AsyncMock()

        modal = Announcement(None, mock_channel, "regular")
        modal.announcement_title = MagicMock(value="my title")
        modal.announcement = MagicMock(value="test")

        await modal.on_submit(mock_interaction)

        mock_channel.send.assert_awaited_once_with(
            content="**my title**\ntest",
            file=None
        )

    async def test_on_submit_embed_submission_skips_leading_newline_without_title(self):
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock()

        mock_interaction = MagicMock(spec=Interaction)
        mock_interaction.response = MagicMock()
        mock_interaction.response.is_done = MagicMock(return_value=False)
        mock_interaction.response.send_message = AsyncMock()
        mock_interaction.followup = MagicMock()
        mock_interaction.followup.send = AsyncMock()

        modal = Announcement(None, mock_channel, "embed")
        modal.announcement_title = MagicMock(value="   ")
        modal.announcement = MagicMock(value="test")

        await modal.on_submit(mock_interaction)

        mock_channel.send.assert_awaited_once()
        self.assertEqual(
            mock_channel.send.await_args.kwargs["embed"].description,
            "test"
        )
        self.assertIsNone(mock_channel.send.await_args.kwargs["file"])

if __name__ == "__main__":
    unittest.main()

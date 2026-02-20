import unittest
from datetime import datetime, timezone

from src.cogs.forum.forum_showcase import format_datetime_in_local_timezone


class TestForumShowcaseTimeFormatting(unittest.TestCase):
    def test_format_naive_utc_datetime_to_utc8(self):
        value = datetime(2024, 12, 20, 11, 0, 0)

        formatted = format_datetime_in_local_timezone(value)

        self.assertEqual(formatted, "2024-12-20 19:00:00 [UTC+8]")

    def test_format_aware_utc_datetime_to_utc8(self):
        value = datetime(2024, 12, 20, 11, 0, 0, tzinfo=timezone.utc)

        formatted = format_datetime_in_local_timezone(value)

        self.assertEqual(formatted, "2024-12-20 19:00:00 [UTC+8]")


if __name__ == "__main__":
    unittest.main()

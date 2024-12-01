import unittest
import unittest.async_case
from asyncio import sleep
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from unittest import IsolatedAsyncioTestCase

from src.utils.scheduler import Schedule, Scheduler, Task

days = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class TestScheduler(IsolatedAsyncioTestCase):
    async def test_spawn_schedule(self):
        scheduler = Scheduler()
        task = Task(lambda: print("Hello, world!"))
        schedule = Schedule(
            date=datetime.now(tz=timezone.utc),
            day="monday",
            task=task,
            frequency="daily",
        )

        await scheduler.spawn_schedule("test", schedule)

        self.assertEqual(schedule.is_running(), True)
        self.assertEqual(len(scheduler.schedules), 1)

    async def test_cancel_schedule(self):
        scheduler = Scheduler()
        task = Task(lambda: print("Good night, world!"))
        schedule = Schedule(
            date=datetime.now(tz=timezone.utc),
            day="monday",
            task=task,
            frequency="daily",
        )

        await scheduler.spawn_schedule("test", schedule)

        self.assertEqual(len(scheduler.schedules), 1)
        self.assertEqual(schedule.is_running(), True)

        scheduler.cancel_schedule("test")

        # Wait for the task to get cancelled before asserting
        await sleep(1)

        self.assertEqual(schedule.is_running(), False)

    async def test_resume_schedule(self):
        scheduler = Scheduler()
        task = Task(lambda: print("Goodbye, world!"))
        schedule = Schedule(
            date=datetime.now(tz=timezone.utc),
            day="monday",
            task=task,
            frequency="daily",
        )
        await scheduler.spawn_schedule("test", schedule)

        self.assertEqual(len(scheduler.schedules), 1)
        self.assertEqual(schedule.is_running(), True)

        scheduler.cancel_schedule("test")

        await sleep(1)
        self.assertEqual(schedule.is_running(), False)
        await scheduler.resume_schedule("test")
        await sleep(1)
        self.assertEqual(schedule.is_running(), True)

    async def test_remove_schedule(self):
        scheduler = Scheduler()
        task = Task(lambda: print("Goodbye, world!"))
        schedule = Schedule(
            date=datetime.now(tz=timezone.utc),
            day="monday",
            task=task,
            frequency="daily",
        )

        await scheduler.spawn_schedule("test", schedule)

        self.assertEqual(len(scheduler.schedules), 1)

        scheduler.remove_schedule("test")

        self.assertEqual(len(scheduler.schedules), 0)

    async def test_reschedule_schedule_daily(self):
        scheduler = Scheduler()
        task = Task(lambda: print("Goodbye, world!"))
        schedule = Schedule(
            date=datetime.now(tz=timezone.utc),
            day=None,
            task=task,
            frequency="daily",
        )

        await scheduler.spawn_schedule("test", schedule)
        self.assertEqual(schedule.is_running(), True)
        self.assertEqual(schedule.get_day(), None)

        schedule.reschedule()

        new_date = datetime.now(tz=timezone.utc).replace(day=schedule._date.day + 1)
        self.assertNotEqual(schedule._date, new_date)

    async def test_reschedule_schedule_weekly(self):
        now = datetime.now(tz=timezone.utc)

        scheduled_time = now + relativedelta(days=5)
        current_day = days[scheduled_time.weekday()]

        scheduler = Scheduler()
        task = Task(lambda: print("Goodbye, world!"))
        schedule = Schedule(
            date=scheduled_time,
            day=current_day,
            task=task,
            frequency="weekly",
        )

        await scheduler.spawn_schedule("test", schedule)

        self.assertEqual(schedule.is_running(), True)
        self.assertEqual(schedule.get_day(), current_day)

        # rescheedule the task to the next week on the same day
        schedule.reschedule()

        self.assertNotEqual(schedule._date, scheduled_time)

        # check if the day is the same
        new_schedule = scheduled_time + relativedelta(weekday=days.index(current_day))
        self.assertEqual(schedule._date.day, new_schedule.day)

    # TODO: add a monthly schedule,
    # this is not working yet
    # since we don't accept a specific day(number) within a month
    #
    async def test_reschedule_schedule_monthly(self):
        now = datetime.now(tz=timezone.utc)
        scheduled_time = now + relativedelta(months=1)
        scheduled_time = scheduled_time.replace(day=1)
        current_day = days[scheduled_time.weekday()]

        scheduler = Scheduler()
        task = Task(lambda: print("Goodbye, world!"))
        schedule = Schedule(
            date=scheduled_time,
            day=current_day,
            task=task,
            frequency="monthly",
        )

        await scheduler.spawn_schedule("test", schedule)

        self.assertEqual(schedule.is_running(), True)
        self.assertEqual(schedule.get_day(), current_day)
        print("before: ", schedule._date)

        schedule.reschedule()

        self.assertNotEqual(schedule._date, scheduled_time)
        new_schedule = scheduled_time
        print("after: ", schedule._date)
        self.assertNotEqual(schedule._date.day, new_schedule.day)


if __name__ == "__main__":
    unittest.main()

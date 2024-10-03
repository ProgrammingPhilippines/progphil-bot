from datetime import datetime, timezone
from typing import Literal, Optional

from dateutil.relativedelta import relativedelta
from discord.ext.tasks import loop

days = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class Task:
    __slots__ = ("func", "schedule")

    def __init__(self, func):
        self.func = func

    async def run(self):
        await self.func()


class Schedule:
    _date: datetime
    _frequency: Literal["daily", "weekly", "monthly"]
    _day: Optional[
        Literal[
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
        ]
        | str
    ]
    _task: Task

    def __init__(
        self,
        date: datetime,
        frequency: Literal["daily", "weekly", "monthly"],
        day: Optional[
            Literal[
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
            | str
        ],
        task: Task,
    ):
        self._date = date
        self._frequency = frequency
        self._day = day
        self._task = task

    async def run(self) -> None:
        self._spawn_loop.start()

    @loop()
    async def _spawn_loop(self):
        if self.is_due():
            await self._task.run()

        self.reschedule()

    def is_due(self) -> bool:
        now = datetime.now(tz=timezone.utc)
        diff = (self._date - now).total_seconds()

        return diff == 0.00 or diff == -1.00

    def is_running(self) -> bool:
        return self._spawn_loop.is_running()

    def reschedule(self) -> None:
        # TODO: Reschedule the task based on the frequency,
        # if the frequency is daily, reschedule the task to the next day
        # and ignore the day parameter
        # if the frequency is weekly/monthly, reschedule the task
        # to the next week
        # and ignore the day parameter if it's not provided

        next_run = self._next_run()
        self._date = next_run

        diff = (self._date - datetime.now(tz=timezone.utc)).total_seconds()

        self._spawn_loop.change_interval(seconds=max(1, diff))

    def get_day(self):
        if self._day is None:
            return None
        return self._day

    def _next_run(self) -> datetime:
        next_run = datetime.now(tz=timezone.utc)

        if self._frequency == "daily":
            next_run += relativedelta(days=1)
            return next_run
        elif self._frequency == "weekly" and self._day is None:
            next_run += relativedelta(weeks=1)
            return next_run
        elif self._frequency == "monthly" and self._day is None:
            next_run = next_run.replace(day=1)
            next_run += relativedelta(months=1)
            return next_run

        if self._day is not None and self._frequency == "weekly":
            next_run += relativedelta(weekday=days.index(self._day))

        # set the day to the first day of the month
        # and set the weekday to the day of the week
        if self._day is not None and self._frequency == "monthly":
            next_run += relativedelta(weekday=days.index(self._day))
            next_run += relativedelta(months=1)
            # next_run = next_run.replace(day=1)

        return next_run

    def cancel(self) -> None:
        if self._spawn_loop.is_running():
            self._spawn_loop.cancel()


class Scheduler:
    schedules: dict[str, Schedule]

    def __init__(self) -> None:
        self.schedules = {}

    async def spawn_schedule(self, key: str, schedule: Schedule):
        if key in self.schedules:
            raise KeyError(f"Schedule with key {key} already exists")
        self.schedules[key] = schedule

        await schedule.run()

    def cancel_schedule(self, key: str) -> None:
        if key not in self.schedules:
            raise KeyError(f"Schedule with key {key} does not exist")

        if self.schedules[key].is_running():
            self.schedules[key].cancel()

    async def resume_schedule(self, key: str) -> None:
        if key not in self.schedules:
            raise KeyError(f"Schedule with key {key} does not exist")

        if not self.schedules[key].is_running():
            await self.schedules[key].run()

    def remove_schedule(self, key: str) -> None:
        if key not in self.schedules:
            raise KeyError(f"Schedule with key {key} does not exist")

        self.cancel_schedule(key)
        self.schedules.pop(key)

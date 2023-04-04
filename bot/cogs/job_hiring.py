# pylint: disable = no-member

from datetime import datetime, timedelta
from textwrap import dedent
from typing import Union

import cloudscraper
from bs4 import BeautifulSoup
from discord import Embed, Interaction, Color, TextChannel, utils
from discord.ext import tasks
from discord.app_commands import command, describe
from discord.ext.commands import Bot, GroupCog

from config import GuildInfo
from database.job_hiring import JobHiringDB
from database.config_auto import Config
from ui.modals.job_hiring import (
    OncePerDay,
    Recurring,
    SpecificDate
)
from ui.views.job_hiring import JobConfig
from utils.decorators import is_staff
from utils.utils import parse

(
    DAILY,
    ONCE,
    RECURRING
) = range(3)

modal_map = {
    DAILY: OncePerDay,
    ONCE: SpecificDate,
    RECURRING: Recurring
}


class Hiring(GroupCog):
    site_to_scrape = "https://ph.indeed.com/jobs?q=tech"

    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = JobHiringDB(self.bot.pool)
        self._toggle_config = Config(self.bot.pool)
        self.time_schedule: Union[str, None] = None
        self.schedule_type: Union[int, None] = None
        self.toggle: Union[bool, None] = None

    async def _refresh(self):
        # Stop the on going loops.
        if self.hiring_task.is_running():
            self.hiring_task.cancel()
        if self.hiring_task2.is_running():
            self.hiring_task2.cancel()            

        config = await self.db.get_config()
        self.toggle = await self._toggle_config.get_config("job_hiring")

        if not config:
            return

        self.time_schedule = config["schedule"]
        self.schedule_type = config["schedule_type"]
        self.hiring_channel = config["channel_id"]

        if self.schedule_type == 0:
            # 1 Means daily.
            utc8 = datetime.strptime(
                self.time_schedule, 
                "%H:%M"
            ).time()

            sched_today = datetime.combine(
                datetime.today(),
                utc8
            )

            schedule = sched_today - timedelta(hours=8)  # Converts the schedule to UTC+0
            self.hiring_task.change_interval(time=schedule.time())
            task = self.hiring_task
        else:
            task = self.hiring_task2

        task.start()

    async def cog_load(self) -> None:
        await self._refresh()

    @tasks.loop()
    async def hiring_task(self):
        if not self.toggle["config_status"]:
            return

        await self.send_job_hiring()

    @tasks.loop()
    async def hiring_task2(self):
        if not self.toggle["config_status"]:
            return

        if self.schedule_type == 1:
            # 1 means ONCE on a set date, once done, it 
            # Will be deleted from the database.
            schedule = datetime.fromtimestamp(int(self.time_schedule))
            await utils.sleep_until(schedule)
            await self.send_job_hiring()
            await self.db.delete(self.hiring_channel)
            await self._refresh()
        else:
            # This is if the schedule is 2, which is recurring.
            # Parse the schedule to seconds, and then sleep and send hiring and repeat.

            parsed = parse(self.time_schedule)
            schedule = datetime.now() + timedelta(seconds=parsed)
            await utils.sleep_until(schedule)
            await self.send_job_hiring()

    async def send_job_hiring(self):
        scraper = cloudscraper.create_scraper()
        response = scraper.get(self.site_to_scrape)

        log_channel = self.bot.get_channel(GuildInfo.log_channel)
        if not response.ok:
            await log_channel.send(f"Job Hiring response error: {response.status_code}")
            await log_channel.send(f"Job Hiring response error: {response.text}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        element = soup.select_one("div.job_seen_beacon a")  # Get the first job

        del soup, response  # Free up memory

        try:  # Raises AttributeError for some reason, so we'll just try again
            job_response = scraper.get(f"https://ph.indeed.com/viewjob?jk={element['data-jk']}")  # Get the job page
            soup = BeautifulSoup(job_response.text, "html.parser")

            job_url = job_response.url
            job_title = soup.select_one('div.jobsearch-DesktopStickyContainer h1').text
            job_company = soup.select_one('div.jobsearch-CompanyInfoContainer a').text
            job_salary = soup.select_one('div#salaryInfoAndJobType span').text
            job_type = (
                soup.select_one('div#jobDetailsSection div:-soup-contains("Job Type")').text  # Job TypeFull-time
                .replace('Job Type', '')  # Full-time
            )

            if not self.hiring_channel:
                return

            channel = self.bot.get_channel(self.hiring_channel)

            if not channel:
                return

            await channel.send(
                embed=Embed(
                    title='Job Hiring',
                    description=dedent(f"""
                    **[{job_title}]({job_url})**
                    *{job_company}*
                    
                    **Salary:** {job_salary}
                    **Job Type:** {job_type}
                    """)
                )
            )
        except AttributeError:
            await self.send_job_hiring()

    @is_staff()
    @command(name="config", description="Get the trivia config")
    async def config(self, interaction: Interaction):
        """
        Gets the hiring config

        :param interaction: Interaction
        """
        schedule_config = await self.db.get_config()

        schedule_map = {
            DAILY: "Daily",
            ONCE: "Once",
            RECURRING: "Recurring"
        }

        if schedule_config is None:
            await interaction.response.send_message(
                "Please setup the trivia first, use /hiring setup.",
                ephemeral=True)
            return

        embed = Embed(
            title="Trivia Config",
            description=dedent(f"""
                        Channel: {self.bot.get_channel(int(schedule_config["channel_id"])).mention}
                        Schedule: {schedule_config["schedule"]}
                        Schedule Type: {schedule_map[schedule_config["schedule_type"]]}
                    """),
            color=Color.random()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @is_staff()
    @command(name="toggle", description="Toggles the auto tagging.")
    async def toggle_config(self, interaction: Interaction):
        """Toggles auto tagging."""

        toggle_map = {
            True: "ON",
            False: "OFF"
        }
        toggle = await self._toggle_config.toggle_config("job_hiring")
        await interaction.response.send_message(
            f"Turned {toggle_map[toggle]} Hiring.",
            ephemeral=True
        )
        await self._refresh()

    @is_staff()
    @command(name="setup", description="Setup the trivia")
    @describe(channel="Channel to send the trivia to")
    async def setup(self, interaction: Interaction, channel: TextChannel) -> None:
        """
        Sets up the job hiring cog

        :param interaction: Interaction
        :param channel: Channel to send the job hiring posts to
        """

        schedule_config = await self.db.get_config()

        if schedule_config is not None:  # This makes that the trivia can only be setup once
            await interaction.response.send_message(
                "Hiring is already setup, use /hiring channel and /hiring schedule to change the channel and schedule.",
                ephemeral=True)
            return

        await self._send_view(interaction, channel, "setup")
        await self._refresh()

    @is_staff()
    @command(name="channel", description="Change the channel to send the job hiring to")
    @describe(channel="Channel to send the job hiring to")
    async def channel(self, interaction: Interaction, channel: TextChannel) -> None:
        """
        Changes the channel to send the job hiring to

        :param interaction: Interaction
        :param channel: Channel to send the job hiring to
        """

        schedule_config = await self.db.get_config()

        if schedule_config is None:
            await interaction.response.send_message(
                "Please setup the job hiring first, use /hiring setup.",
                ephemeral=True)
            return

        await self.db.update(
            channel_id=channel.id,
            schedule=schedule_config["schedule"],
            schedule_type=schedule_config["schedule_type"]
        )

        await interaction.response.send_message(
            f"Changed the channel to {channel.mention}",
            ephemeral=True
        )
        await self._refresh()

    @is_staff()
    @command(name="schedule", description="Change the schedule of the job hiring")
    async def schedule(self, interaction: Interaction) -> None:
        """
        Changes the schedule of the job hiring

        :param interaction: Interaction
        """

        schedule_config = await self.db.get_config()

        if schedule_config is None:
            await interaction.response.send_message(
                "Please setup the job hiring first, use /hiring setup.",
                ephemeral=True)
            return

        await self._send_view(interaction, self.bot.get_channel(int(schedule_config["channel_id"])), "schedule")

    async def _send_view(self, interaction: Interaction, channel: TextChannel, sched_type: str):
        embed = Embed(
            title="Job Hiring Schedule",
            description=dedent("""
            :one: - Every Day at a specific time
            :two: - Once on a specific day
            :three: - Every N [months|days|hours|minutes|seconds]
            """),
            color=Color.random()
        )
        view = JobConfig(self.bot.pool, channel, sched_type)
        await interaction.response.send_message(embed=embed, view=view)
        await view.wait()
        await self._refresh()


async def setup(bot: Bot):
    await bot.add_cog(Hiring(bot))

from textwrap import dedent
from typing import Union

import cloudscraper
import discord
from bs4 import BeautifulSoup
from discord import Embed, Interaction
from discord.app_commands import command, describe
from discord.ext.commands import Bot, GroupCog

from config import GuildInfo
from bot.database.job_hiring import JobHiringDB
from database.config_auto import Config
from ui.modals.job_hiring import (
    OncePerDay,
    Recurring,
    SpecificDate
)
from bot.ui.views.job_hiring import JobConfig
from utils.decorators import is_staff

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
        self.db: Union[JobHiringDB, None] = None
        self._toggle_config: Union[Config, None] = None

    async def cog_load(self) -> None:
        self.db = JobHiringDB(self.bot.pool)
        self._toggle_config = Config(self.bot.pool)

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

            # will be changed to the actual channel
            await log_channel.send(
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
            color=discord.Color.random()
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

    @is_staff()
    @command(name="setup", description="Setup the trivia")
    @describe(channel="Channel to send the trivia to")
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
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

    @is_staff()
    @command(name="channel", description="Change the channel to send the job hiring to")
    @describe(channel="Channel to send the job hiring to")
    async def channel(self, interaction: Interaction, channel: discord.TextChannel) -> None:
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

    async def _send_view(self, interaction: Interaction, channel: discord.TextChannel, sched_type: str):
        embed = Embed(
            title="Job Hiring Schedule",
            description=dedent("""
            :one: - Every Day at a specific time
            :two: - Once on a specific day
            :three: - Every N [months|days|hours|minutes|seconds]
            """),
            color=discord.Color.random()
        )
        await interaction.response.send_message(embed=embed, view=JobConfig(self.bot.pool, channel, sched_type))


async def setup(bot: Bot):
    await bot.add_cog(Hiring(bot))

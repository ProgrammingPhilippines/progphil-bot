from textwrap import dedent

import cloudscraper
from bs4 import BeautifulSoup
from discord import Embed
from discord.app_commands import command
from discord.ext.commands import Bot, GroupCog

from bot.config import GuildInfo


class JobHiring(GroupCog):
    site_to_scrape = "https://ph.indeed.com/jobs?q=tech"

    def __init__(self, bot: Bot):
        self.bot = bot

    @command()
    async def job_hiring(self, interaction):
        await interaction.response.send_message('Sending job hiring...', ephemeral=True)
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

        try:
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


async def setup(bot: Bot):
    await bot.add_cog(JobHiring(bot))

from datetime import datetime
from logging import Logger

from discord import Button, ButtonStyle, ChannelType, Interaction
from discord.app_commands import AppCommandChannel, AppCommandThread
from discord.ui import ChannelSelect, View, button, select

from src.data.forum.forum_showcase import ForumShowcaseDB, ShowcaseForum


class ForumShowcaseAddView(View):
    showcase_forums: list[ShowcaseForum]

    def __init__(
        self,
        existing_forums: list[AppCommandChannel | AppCommandThread],
        forum_showcase_id: int,
        forum_showcase_db: ForumShowcaseDB,
        logger: Logger,
    ):
        super().__init__(timeout=480)
        self.selection = existing_forums
        self.forum_showcase_id = forum_showcase_id
        self.forum_showowcase_db = forum_showcase_db
        self.logger = logger

        select_menu = [
            item for item in self.children if isinstance(item, ChannelSelect)
        ][0]
        select_menu.default_values = self.selection

    @select(
        cls=ChannelSelect,
        placeholder="Select forum...",
        max_values=25,
        channel_types=[ChannelType.forum],
    )
    async def select_forums(self, interaction: Interaction, selection: ChannelSelect):
        self.selection = [tag for tag in selection.values]

        await interaction.response.send_message(
            f"Selected {len(self.selection)} forums.", ephemeral=True
        )

    @button(label="Submit", style=ButtonStyle.green)
    async def submit(self, interaction: Interaction, button: Button):
        now = datetime.now()
        self.showcase_forums = [
            ShowcaseForum(
                forum_id=forum.id, showcase_id=self.forum_showcase_id, created_at=now
            )
            for forum in self.selection
        ]
        for showcase_forum in self.showcase_forums:
            try:
                await self.forum_showowcase_db.add_forum(showcase_forum)
            except Exception as e:
                self.logger.error(
                    f"Failed to add forum {showcase_forum.forum_id} to showcase.\n {e}"
                )
                await interaction.response.send_message(
                    f"Failed to add forum {showcase_forum.forum_id} to showcase.",
                    ephemeral=True,
                )
                return

        msg = f"Added {len(self.selection)} forums to showcase."
        await interaction.response.send_message(msg, ephemeral=True)

from typing import Callable

from discord import Interaction, ButtonStyle, ChannelType
from discord import TextStyle, Member, Guild, Role
from discord.ui import (
    Select,
    View,
    Modal,
    Button,
    TextInput,
    MentionableSelect,
    ChannelSelect,
    select,
    button,
)

from src.data.admin.settings import Settings
from src.data.forum.post_assist import PostAssistDB


class PostAssistState:
    def __init__(
        self,
        forum: int = None,
        tag_message: str = None,
        custom_msg: str = None,
        existing_tags: list[Role] | list[Member] = [],
        enable_accept_solutions: bool = False,
        enable_mark_as_solved: bool = False,
        finished: bool = False,
        failed: bool = False,
    ):
        self.forum: int = forum
        self.tag_list: list[tuple[int, str]] = []
        self.existing_tags: list[Role] | list[Member] = existing_tags or []
        self.tag_message: str = tag_message
        self.custom_msg: str = custom_msg
        self.enable_accept_solutions: bool = enable_accept_solutions
        self.enable_mark_as_solved: bool = enable_mark_as_solved
        self.finished = finished
        self.failed = failed


class ConfigurePostAssist(View):
    def __init__(
        self,
        forum: int = None,
        tag_message: str = None,
        custom_msg: str = None,
        db: PostAssistDB = None,
    ):
        super().__init__(timeout=480)
        self.db = db
        self.state = PostAssistState(
            forum=forum,
            tag_message=tag_message,
            custom_msg=custom_msg,
            existing_tags=[],
            enable_accept_solutions=False,
        )

    @select(
        cls=ChannelSelect,
        placeholder="Select forum...",
        channel_types=[ChannelType.forum],
    )
    async def select_forum(self, interaction: Interaction, selection: ChannelSelect):
        if self.state.forum and self.state.forum != selection.values[0].id:
            return await interaction.response.send_message(
                f"Please select this forum -> {interaction.guild.get_channel(self.state.forum).mention}.",
                ephemeral=True,
            )

        selected_forum = selection.values[0].id

        if await self.db.config_by_forum(selected_forum):
            await interaction.response.send_message(
                "There is already a configuration for this forum.",
                ephemeral=True,
            )
            self.state.failed = True
            return self.stop()

        self.state.forum = selected_forum
        modal = PostAssistMessage(self.state)
        await interaction.response.send_modal(modal)
        await modal.wait()

        self.stop()


class PostAssistMessage(Modal, title="Post Assist Message"):
    def __init__(self, options: PostAssistState):
        super().__init__(timeout=480)

        self.state = options
        self.message = TextInput(
            label="Post Assist Message",
            placeholder="Enter message here...",
            min_length=0,
            max_length=2000,
            style=TextStyle.long,
            required=False,
            default=self.state.custom_msg,
        )
        self.add_item(self.message)

    async def on_submit(self, interaction: Interaction) -> None:
        self.state.custom_msg = self.message.value
        view = PostAssistTags(self.state)
        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()


class PostAssistTags(View):
    def __init__(self, options: PostAssistState):
        super().__init__(timeout=480)

        self.state = options
        self.selection = [tag for tag in self.state.existing_tags]

        select_menu = [
            item for item in self.children if isinstance(item, MentionableSelect)
        ][0]
        select_menu.default_values = self.state.existing_tags

    @select(cls=MentionableSelect, placeholder="Select member/roles...", max_values=25)
    async def select_entities(
        self, interaction: Interaction, selection: MentionableSelect
    ):
        self.selection = [tag for tag in selection.values]

        await interaction.response.send_message(
            f"Selected {len(self.selection)} entities.", ephemeral=True
        )

    @button(label="Submit", style=ButtonStyle.green)
    async def submit(self, interaction: Interaction, button: Button):
        self.state.tag_list = [
            (entity.id, "member" if isinstance(entity, Member) else "role")
            for entity in self.selection
        ]

        modal = PostAssistTagMessage(self.state, required=bool(self.state.tag_list))
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.stop()


class PostAssistTagMessage(Modal, title="Set Tag Message"):
    def __init__(self, options: PostAssistState, required: bool):
        super().__init__(timeout=480)

        self.state = options
        self.message = TextInput(
            label="Post Assist Tag Message",
            placeholder="Enter message here...",
            min_length=0,
            max_length=500,
            style=TextStyle.long,
            required=required,
            default=self.state.tag_message,
        )

        self.add_item(self.message)

    async def on_submit(self, interaction: Interaction) -> None:
        self.state.tag_message = self.message.value

        view = PostAssistMarkAsSolution(self.state)
        await interaction.response.send_message(
            "Enable Accept Solution feature?", view=view, ephemeral=True
        )
        await view.wait()
        self.stop()


class PostAssistMarkAsSolution(View):
    def __init__(self, options: PostAssistState):
        super().__init__(timeout=480)
        self.state = options

    @button(label="Yes")
    async def enable(self, interaction: Interaction, button: Button):
        self.state.enable_accept_solutions = True

        await interaction.response.send_message(
            "Accept as solution will be enabled.", ephemeral=True
        )

        enable_mark_as_solved_button = PostAssistEnableMarkAsSolvedButton(self.state)
        await interaction.followup.send(
            "Enable Mark as Solved feature?",
            view=enable_mark_as_solved_button,
            ephemeral=True,
        )
        await enable_mark_as_solved_button.wait()
        self.stop()

    @button(label="No")
    async def disable(self, interaction: Interaction, button: Button):
        self.state.enable_accept_solutions = False
        self.state.finished = True
        await interaction.response.send_message(
            "Accept solutions disabled.", ephemeral=True
        )

        enable_mark_as_solved_button = PostAssistEnableMarkAsSolvedButton(self.state)
        await interaction.followup.send(
            "Enable Mark as Solved feature?",
            view=enable_mark_as_solved_button,
            ephemeral=True,
        )
        await enable_mark_as_solved_button.wait()
        self.stop()


class PostAssistEnableMarkAsSolvedButton(View):
    def __init__(self, options: PostAssistState):
        super().__init__(timeout=480)
        self.state = options

    @button(label="Yes")
    async def enable_mark_as_solved(self, interaction: Interaction, button: Button):
        await interaction.response.defer()

        self.state.enable_mark_as_solved = True
        self.state.finished = True

        await interaction.followup.send(
            "Mark as solved will be enabled.", ephemeral=True
        )

        self.stop()

    @button(label="No")
    async def disable_mark_as_solved(self, interaction: Interaction, button: Button):
        self.state.enable_mark_as_solved = False
        self.state.finished = True
        await interaction.response.send_message(
            "Mark as solved disabled.", ephemeral=True
        )
        self.stop()


class ConfigurationPagination(View):
    def __init__(self, data: list[dict], getter: Callable):
        self.data = data
        self.getter = getter
        self.page = 0
        self.max_len = len(data)
        super().__init__(timeout=480)

    @button(label="Previous")
    async def previous(self, interaction: Interaction, button: Button):
        self.page -= 1
        self.next.disabled = False

        if self.page == 0:
            button.disabled = True

        await interaction.response.edit_message(
            content=format_data(self.data[self.page], interaction.guild, self.getter),
            view=self,
        )

    @button(label="Next")
    async def next(self, interaction: Interaction, button: Button):
        self.page += 1
        self.previous.disabled = False

        if self.page >= self.max_len - 1:
            self.page = self.max_len - 1
            button.disabled = True

        await interaction.response.edit_message(
            content=format_data(self.data[self.page], interaction.guild, self.getter),
            view=self,
        )


def get_forums(db: Settings, guild: Guild) -> View:
    """Gets all forums."""

    async def select_callback(interaction: Interaction):
        await db.set_setting("dev_help_forum", int(forum_selection.values[0]))
        await interaction.response.edit_message(content=f"Success...", view=None)
        view.stop()

    view = View()
    forum_selection = Select(placeholder="Select Forum...")
    forum_selection.callback = select_callback

    for forum in guild.forums:
        forum_selection.add_option(label=forum.name, value=str(forum.id))

    view.add_item(forum_selection)
    return view


def format_data(data: dict, guild: Guild, getter: Callable):
    forum = guild.get_channel(data["forum_id"])
    tags = data["tags"]
    tag_message = data["tag_message"]
    reply = data["reply"]
    tag_mentions = []

    for tag in tags:
        entity = getter(guild, tag)
        tag_mentions.append(f"{entity.name} [{tag['entity_type'].title()}]\n")

    tag_mentions_str = "\t".join(tag_mentions)

    message = (
        f"```Configuration ID: {data['id']}\n"
        f"Forum: {forum.name}\n"
        f"Reply: {reply}\n"
        f"Tags: \n\t{tag_mentions_str}\n"
        f"Tag Message: {tag_message}\n```"
    )

    return message

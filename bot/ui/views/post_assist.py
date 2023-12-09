from typing import Callable
from textwrap import dedent

from discord import Interaction, ButtonStyle, ChannelType, TextStyle, Member, Guild
from discord.ui import View, Modal, Button, TextInput, ChannelSelect, MentionableSelect, select, button


class ConfigurePostAssist(View):
    def __init__(self, forum: int = None, tag_message: str = None, custom_msg: str = None):
        self.forum: int = forum
        self.tag_list: list[tuple[int, str]] = []
        self.tag_message: str = tag_message
        self.custom_msg: str = custom_msg
        self.finished = False
        super().__init__()

    @select(cls=ChannelSelect, placeholder="Select forum...", channel_types=[ChannelType.forum])
    async def select_forum(self, interaction: Interaction, selection: ChannelSelect):
        if self.forum and self.forum != selection.values[0].id:
            return await interaction.response.send_message(
                f"Please select this forum -> {interaction.guild.get_channel(self.forum).mention}.",
                ephemeral=True
            )

        self.forum = selection.values[0].id
        modal = PostAssistMessage(self)
        await interaction.response.send_modal(modal)
        await modal.wait()


class PostAssistMessage(Modal, title="Post Assist Message"):
    def __init__(self, config_class: ConfigurePostAssist):
        self.config_class = config_class
        self.message = TextInput(
            label="Post Assist Message",
            placeholder="Enter message here...",
            min_length=0,
            max_length=2000,
            style=TextStyle.long,
            required=False,
            default=self.config_class.custom_msg
        )

        super().__init__(timeout=512)
        self.add_item(self.message)

    async def on_submit(self, interaction: Interaction) -> None:
        self.config_class.custom_msg = self.message.value
        view = PostAssistTags(self.config_class)
        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()


class PostAssistTags(View):
    def __init__(self, config_class: ConfigurePostAssist):
        self.config_class = config_class
        self.selection = []
        super().__init__()

    @select(cls=MentionableSelect, placeholder="Select member/roles...", max_values=25)
    async def select_entities(self, interaction: Interaction, selection: MentionableSelect):
        self.selection.extend(selection.values)

        await interaction.response.send_message(
            f"Selected {len(selection.values)} entities.",
            ephemeral=True
        )

    @button(label="Submit", style=ButtonStyle.green)
    async def submit(self, interaction: Interaction, button: Button):
        self.config_class.tag_list = [
            (
                entity.id, "member"
                if isinstance(entity, Member)
                else "role"
            ) for entity in self.selection
        ]

        self.stop()
        modal = PostAssistTagMessage(self.config_class, required=bool(self.config_class.tag_list))
        await interaction.response.send_modal(modal)
        await modal.wait()


class PostAssistTagMessage(Modal, title="Set Tag Message"):
    def __init__(self, config_class: ConfigurePostAssist, required: bool):
        self.config_class = config_class
        self.message = TextInput(
            label="Post Assist Tag Message",
            placeholder="Enter message here...",
            min_length=0,
            max_length=500,
            style=TextStyle.long,
            required=required,
            default=self.config_class.tag_message
        )

        super().__init__()
        self.add_item(self.message)

    async def on_submit(self, interaction: Interaction) -> None:
        self.config_class.tag_message = self.message.value
        await interaction.response.send_message("Success...", ephemeral=True)
        self.config_class.stop()
        self.config_class.finished = True


class ConfigurationPagination(View):
    def __init__(self, data: list[dict], getter: Callable):
        self.data = data
        self.getter = getter
        self.page = 1
        self.max_len = len(data)
        super().__init__()

    @button(label="Previous")
    async def previous(self, interaction: Interaction, button: Button):
        self.page -= 1

        if self.page == 0:
            button.disabled = True

        await interaction.response.edit_message(
            content=format_data(self.data[self.page], interaction.guild, self.getter),
            view=self
        )

    @button(label="Next")
    async def next(self, interaction: Interaction, button: Button):
        self.page += 1
        self.previous.disabled = True

        if self.page == self.max_len:
            button.disabled = True

        await interaction.response.edit_message(
            content=format_data(self.data[self.page], interaction.guild, self.getter),
            view=self
        )


def format_data(data: dict, guild: Guild, getter: Callable):
    forum = guild.get_channel(data["forum_id"])
    tags = data["tags"]
    tag_message = data["tag_message"]
    reply = data["reply"]
    tag_mentions = []

    for tag in tags:
        entity = getter(guild, tag)
        tag_mentions.append(f"{entity.name} - {tag['entity_type'].title()}\n")

    tag_mentions_str = '\t'.join(tag_mentions)

    message = (
        f"```Forum: {forum.name}\n"
        f"Reply: {reply}\n"
        f"Tags: \n\t{tag_mentions_str}\n"
        f"Tag Message: {tag_message}\n```"
    )

    return message

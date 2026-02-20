import asyncio
from logging import Logger

from discord import (
    Forbidden,
    ForumChannel,
    Guild,
    HTTPException,
    Interaction,
    Member,
    Message,
    Role,
    Thread,
)
from discord.app_commands import ContextMenu, command, describe
from discord.enums import AppCommandType
from discord.ext.commands import Bot, Cog, GroupCog
from discord.ui.select import Select
from discord.ui.view import View

from src.data.admin.config_auto import Config
from src.data.forum.post_assist import PostAssistDB
from src.ui.views.mark_as_solution import MarkAsSolution
from src.ui.views.post_assist import (
    ConfigurationPagination,
    ConfigurePostAssist,
    PostAssistMessage,
    PostAssistState,
    format_data,
)
from src.ui.views.solver import PersistentSolverView
from src.utils.decorators import is_staff

AUTHOR_PLACEHOLDER = "[[@author]]"


def get_tag_options(db: PostAssistDB, forum: ForumChannel) -> View | None:
    """Gets all tag options for the given forum."""

    async def select_callback(interaction: Interaction):
        await db.set_mark_as_solved_tag(forum.id, int(tag_selection.values[0]))
        await interaction.response.edit_message(content=f"Success...", view=None)
        view.stop()

    view = View()
    tag_selection = Select(placeholder="Select Tag...")
    tag_selection.callback = select_callback

    if not forum.available_tags:
        return

    for a_tag in forum.available_tags:
        tag_selection.add_option(
            label=f"{a_tag.emoji}{a_tag.name}" if a_tag.emoji else a_tag.name,
            value=a_tag.id,
        )

    view.add_item(tag_selection)
    return view


def _getter(guild: Guild, entry: dict) -> Member | Role:
    """Gets the object type and returns it."""

    if entry["entity_type"] == "role":
        getter = guild.get_role
    else:
        getter = guild.get_member

    return getter(entry["entity_id"])


class ForumAssist(GroupCog, name="forum-assist"):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.logger: Logger = self.bot.logger  # type: ignore
        self.db = PostAssistDB(self.bot.pool)  # type: ignore
        self.config = Config(self.bot.pool)  # type: ignore
        ctx_menu = ContextMenu(
            name="Accept Solution",
            callback=self.accept_solution,
            type=AppCommandType.message,
        )
        self.bot.tree.add_command(ctx_menu)
        self.ctx_menu = ctx_menu

    async def load(self):
        await self.bot.wait_until_ready()

        staff_roles: list[int] = self.bot.config.guild.staff_roles

        for view in await self.db.get_persistent_mark_as_solved_views():
            self.bot.add_view(
                PersistentSolverView(
                    view["thread_id"],
                    view["author_id"],
                    self.db,
                    staff_roles,
                    self.logger,
                ),
                message_id=view["message_id"],
            )

    async def cog_load(self):
        asyncio.create_task(self.load())

    @Cog.listener()
    async def on_thread_create(self, thread: Thread):
        await self._send_mark_ask_solved_button(thread)
        await self._notify_subscribers(thread)

    async def _send_mark_ask_solved_button(self, thread: Thread):
        staff_roles: list[int] = self.bot.config.guild.staff_roles

        if not isinstance(thread.parent, ForumChannel):
            return

        if not thread.owner_id:
            return

        async def try_send() -> Message:
            for _ in range(5):  # max of 5 retries
                try:
                    return await thread.send(
                        "Mark this post as Solved!",
                        view=PersistentSolverView(
                            thread.id,
                            thread.owner_id,
                            self.db,
                            staff_roles,
                            self.logger,
                        ),
                    )
                except Forbidden:
                    pass

        _, is_enabled = await self.db.is_mark_as_solved_enabled_for_forum(
            thread.parent_id
        )

        if not is_enabled:
            return

        global_config = await self.config.get_config("auto_tagging")
        if not global_config["config_status"]:
            return

        entry = await self.db.config_by_forum(thread.parent.id)
        if not entry:
            return

        if not await self.db.get_mark_as_solved_tag(thread.parent_id):
            return

        bot_message = await try_send()

        if not bot_message:
            return

        await bot_message.pin()
        await self.db.add_persistent_mark_as_solved_view(
            thread.id, bot_message.id, thread.owner_id
        )

    async def _notify_subscribers(self, thread: Thread):
        config = await self.config.get_config("auto_tagging")

        if not config["config_status"]:
            return

        entry = await self.db.config_by_forum(thread.parent.id)

        if not entry:
            return

        reply = await self.db.get_reply(entry["id"])
        tags = await self.db.get_tags(entry["id"])
        tag_message = await self.db.get_tag_message(entry["id"])

        thread_msg = thread.get_partial_message(thread.id)

        if reply and AUTHOR_PLACEHOLDER in reply:
            reply = reply.replace(AUTHOR_PLACEHOLDER, thread_msg.thread.owner.mention)

        # Sometimes the pinning and reply fails
        # when the thread is created and the bot
        # tries to reply before the author's first message gets sent.
        # So we try at a maximum of 5 times to pin and reply.
        for _ in range(5):
            try:
                await thread_msg.pin()

                if reply:
                    await thread.send(reply)

                break
            except (Forbidden, HTTPException):
                pass

        if tags and tag_message:
            message = ""

            for tag in tags:
                message += f"{_getter(thread.guild, tag).mention}\n"

            message += tag_message

            await thread.send(message)

    @is_staff()
    @command(name="toggle", description="Toggles the auto tagging.")
    async def toggle_config(self, interaction: Interaction):
        """Toggles auto tagging."""

        toggle_map = {True: "ON", False: "OFF"}

        toggle = await self.config.toggle_config("auto_tagging")

        await interaction.response.send_message(
            f"Turned {toggle_map[toggle]} Auto Tagging.",
            ephemeral=True,
        )

    @is_staff()
    @command(name="new", description="Add a new configuration.")
    async def create_new(self, interaction: Interaction):
        """Adds an entry to the database."""

        await interaction.response.defer(ephemeral=True)

        view = ConfigurePostAssist(db=self.db)

        await interaction.followup.send(
            "Configure Post Assist", view=view, ephemeral=True
        )
        await view.wait()

        forum = view.state.forum
        reply = view.state.custom_msg
        tags = view.state.tag_list
        tag_message = view.state.tag_message
        enable_accept_solutions = view.state.enable_accept_solutions

        if view.state.failed:
            return await interaction.followup.send(
                "Failed to configure post assist.",
                ephemeral=True,
            )

        if not (view.state.tag_list or view.state.custom_msg):
            return await interaction.followup.send(
                "You must provide either tags or a custom message.",
                ephemeral=True,
            )

        if view.state.finished:
            await self.db.add_configuration(
                forum_id=forum,
                entities=tags,
                entity_tag_message=tag_message,
                reply=reply,
                enable_accept_solutions=enable_accept_solutions,
                enable_mark_as_solved=view.state.enable_mark_as_solved,
            )

            if view.state.enable_mark_as_solved:
                forum_channel = await self.bot.fetch_channel(view.state.forum)
                if isinstance(forum_channel, ForumChannel):
                    tag_view = get_tag_options(self.db, forum_channel)
                    if tag_view:
                        await interaction.followup.send(view=tag_view, ephemeral=True)
                        await tag_view.wait()

                    await interaction.followup.send(
                        "Mark as solved button configured.", ephemeral=True
                    )

            await interaction.followup.send("Success!", ephemeral=True)
            return

        await interaction.followup.send("Cancelled.", ephemeral=True)

    @is_staff()
    @command(name="delete", description="Deletes a configuration.")
    @describe(config_id="The configuration ID")
    async def delete(self, interaction: Interaction, config_id: int):
        """Removes an entry from the database.

        :param config_id: The configuration ID from the database.
        """

        if await self.db.get_config(config_id):
            message = f"Successfully removed entry with ID: {config_id}"
            await self.db.delete_configuration(config_id)
        else:
            message = f"Configuration ID: {config_id} may not exist."

        await interaction.response.send_message(message, ephemeral=True)

    @is_staff()
    @command(name="list", description="Views all configurations.")
    async def view_all(self, interaction: Interaction):
        """Views all PPH entries."""

        result = await self.db.list_configurations()

        if not result:
            return await interaction.response.send_message(
                "There are no configurations.",
                ephemeral=True,
            )

        view = ConfigurationPagination(result, _getter)
        view.previous.disabled = True

        if not result[1:]:
            view.next.disabled = True

        await interaction.response.send_message(
            format_data(result[0], interaction.guild, _getter),
            view=view,
            ephemeral=True,
        )
        await view.wait()

    @is_staff()
    @command(name="edit", description="Edits a configuration.")
    @describe(config_id="The configuration ID")
    async def edit(self, interaction: Interaction, config_id: int):
        """Edits an entry from the database.

        :param config_id: The configuration ID from the database.
        """

        # await interaction.response.defer(ephemeral=True)
        try:
            config = await self.db.get_config(config_id)
            if not config:
                self.bot.logger.info(f"Configuration ID: {config_id} may not exist.")
                return await interaction.response.send_message(
                    f"Configuration ID: {config_id} may not exist.",
                    ephemeral=True,
                )
        except Exception as e:
            self.bot.logger.error(e)

        forum_id = config["forum_id"]
        tag_message = await self.db.get_tag_message(config_id)
        custom_message = await self.db.get_reply(config_id)
        tags = await self.db.get_tags(config_id)
        existing_tags: list[Role] | list[Member] = []

        # Get current configuration values
        current_enable_accept_solutions = config.get("enable_accept_solutions", False)

        current_mark_as_solved = config.get("enable_mark_as_solved", False)

        for tag in tags:
            tag_id = tag["entity_id"]
            if tag["entity_type"] == "role":
                existing_tags.append(interaction.guild.get_role(tag_id))
            elif tag["entity_type"] == "member":
                existing_tags.append(interaction.guild.get_member(tag_id))

        state = PostAssistState(
            forum=forum_id,
            tag_message=tag_message,
            custom_msg=custom_message,
            existing_tags=existing_tags,
            enable_accept_solutions=current_enable_accept_solutions,
            enable_mark_as_solved=current_mark_as_solved,
        )

        modal = PostAssistMessage(state)
        await interaction.response.send_modal(modal)
        await modal.wait()

        reply = modal.state.custom_msg
        tags = modal.state.tag_list
        tag_message = modal.state.tag_message

        if not (modal.state.tag_list or modal.state.custom_msg):
            return await interaction.followup.send(
                "You must provide either tags or a custom message.",
                ephemeral=True,
            )

        if modal.state.finished:
            await interaction.followup.send("Success!", ephemeral=True)
            await self.db.update_configuration(
                id=config_id,
                forum_id=forum_id,
                entities=tags,
                entity_tag_message=tag_message,
                reply=reply,
                enable_accept_solutions=modal.state.enable_accept_solutions,
                enable_mark_as_solved=modal.state.enable_mark_as_solved,
            )

            if modal.state.enable_mark_as_solved:
                forum_channel = await self.bot.fetch_channel(forum_id)
                if isinstance(forum_channel, ForumChannel):
                    tag_view = get_tag_options(self.db, forum_channel)
                    if tag_view:
                        await interaction.followup.send(view=tag_view, ephemeral=True)
                        await tag_view.wait()

                await interaction.followup.send(
                    "Mark as solved button enabled for this forum.", ephemeral=True
                )
            else:
                await self.db.delete_mark_as_solved_tag(forum_id)
                await interaction.followup.send(
                    "Mark as solved button disabled for this forum.", ephemeral=True
                )

            return

        await interaction.followup.send("Cancelled.", ephemeral=True)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.ctx_menu.name, type=self.ctx_menu.type
        )  # remove it on unload

    async def _get_current_solution_from_pins(self, thread: Thread) -> Message | None:
        """Check pinned messages to find the current accepted solution.

        Returns the pinned message that has a ✅ reaction from the bot,
        or None if no solution is currently accepted.

        Note: We need to fetch full message objects because pins() returns
        incomplete reaction data according to Discord API documentation.
        """
        try:
            pinned_messages = await thread.pins()
            self.logger.info(
                f"Found {len(pinned_messages)} pinned messages in thread {thread.id}"
            )

            for pinned_msg in pinned_messages:
                # Skip the original thread message (it's always pinned)
                if pinned_msg.id == thread.id:
                    continue

                try:
                    full_message = await thread.fetch_message(pinned_msg.id)

                    for reaction in full_message.reactions:
                        emoji_str = str(reaction.emoji)

                        if emoji_str not in ["✅", "✔️", "☑️"]:
                            continue

                        if self.bot.user:
                            async for user in reaction.users():
                                if user.id == self.bot.user.id:
                                    self.logger.info(
                                        f"Found existing solution: message {full_message.id}"
                                    )
                                    return full_message

                except (Forbidden, HTTPException) as e:
                    self.logger.warning(f"Failed to fetch message {pinned_msg.id}: {e}")
                    continue

            self.logger.info("No existing solution found in pinned messages")

        except (Forbidden, HTTPException) as e:
            self.logger.warning(
                f"Failed to access pinned messages in thread {thread.id}: {e}"
            )

        return None

    # Only allow the author or staff
    def _can_accept_solution(
        self, interaction: Interaction, thread_author_id: int, staff_roles: list[int]
    ) -> bool:
        if interaction.user.id == thread_author_id:
            return True

        user_permissions = getattr(interaction.user, "guild_permissions", None)
        if user_permissions and user_permissions.administrator:
            return True

        user_roles = {role.id for role in getattr(interaction.user, "roles", [])}
        return any(role_id in user_roles for role_id in staff_roles)

    async def accept_solution(self, interaction: Interaction, message: Message) -> None:
        thread = interaction.channel
        is_thread = isinstance(thread, Thread)
        thread_id = thread.id if is_thread else None
        thread_author_id = thread.owner_id if is_thread else None
        message_id = message.id
        forum = thread.parent if is_thread else None
        staff_roles: list[int] = self.bot.config.guild.staff_roles  # type: ignore

        if (
            not is_thread
            or not thread_author_id
            or not thread_id
            or not forum
            or not isinstance(forum, ForumChannel)
        ):
            return await interaction.response.send_message(
                "This command can only be used in threads.", ephemeral=True
            )

        can_accept_solution = self._can_accept_solution(
            interaction=interaction,
            thread_author_id=thread_author_id,
            staff_roles=staff_roles,
        )
        if not can_accept_solution:
            return await interaction.response.send_message(
                "Only the thread owner or staff can accept a solution.",
                ephemeral=True,
            )

        if thread.archived:
            return await interaction.response.send_message(
                "This thread is archived.", ephemeral=True
            )

        if message.author.bot:
            return await interaction.response.send_message(
                "Cannot mark a bot's post as a solution.", ephemeral=True
            )

        if message_id == thread_id:
            return await interaction.response.send_message(
                "Cannot mark the original post as a solution.", ephemeral=True
            )

        mark_as_solution_config = await self.db.is_mark_as_solution_enabled(forum.id)
        is_enabled = mark_as_solution_config[1]

        if not is_enabled:
            return await interaction.response.send_message(
                "Accept Solution is not enabled here.", ephemeral=True
            )

        mark_as_solution_view = MarkAsSolution(thread=thread, message=message)
        await interaction.response.send_message(
            "Are you sure you want to mark this as a solution?",
            view=mark_as_solution_view,
            ephemeral=True,
        )
        await mark_as_solution_view.wait()

        if not mark_as_solution_view.confirmed:
            return

        current_solution_message = await self._get_current_solution_from_pins(thread)

        if current_solution_message:
            try:
                await current_solution_message.unpin()
            except (Forbidden, HTTPException) as e:
                self.logger.warning(
                    f"Failed to unpin previous solution {current_solution_message.id}: {e}"
                )

            if self.bot.user:
                try:
                    await current_solution_message.remove_reaction("✅", self.bot.user)
                    self.logger.info(
                        f"Removed ✅ from previous solution: {current_solution_message.id}"
                    )
                except (Forbidden, HTTPException) as e:
                    self.logger.warning(
                        f"Failed to remove ✅ from previous solution {current_solution_message.id}: {e}"
                    )

        try:
            await message.add_reaction("✅")
            await message.pin()
            self.logger.info(f"Marked message {message.id} as solution")
        except (Forbidden, HTTPException) as e:
            self.logger.error(f"Failed to mark message {message.id} as solution: {e}")

        mark_as_solved_button = PersistentSolverView(
            thread_id,
            thread_author_id,
            self.db,
            staff_roles,
            self.logger,
        )

        await interaction.followup.send(
            f"{interaction.user.mention} marked this as a solution.",
            view=mark_as_solved_button,
            ephemeral=False,
        )


async def setup(bot: Bot):
    await bot.add_cog(ForumAssist(bot))

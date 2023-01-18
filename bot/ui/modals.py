from discord import Interaction, TextStyle, Attachment, TextChannel
from discord.ui import Modal, TextInput, View, RoleSelect


class Announcement(Modal, title='Announcement'):
    announcement_title = TextInput(
        label='Title',
        placeholder='Title',
        required=True,
    )
    announcement = TextInput(
        label='Announcement',
        placeholder='Announcement',
        required=True,
        style=TextStyle.paragraph
    )

    def __init__(
            self,
            attachment: Attachment,
            channel: TextChannel,
            mention: str = None
            ):
        super().__init__()
        self.attachment = attachment
        self.channel = channel
        self.mention = mention

    async def on_submit(self, interaction: Interaction) -> None:
        photo = None
        mentions = []

        if self.attachment:  # If the user has uploaded an attachment
            photo = await self.attachment.to_file()

        if self.mention == "roles":
            async def role_callback(interaction: Interaction):
                """Represents the role select callback.

                This will get called when "Role Select Dropdown" gets submitted
                Once submitted, roles.values will hold a list of selected roles.
                We'll add the mentioned roles to the pre-defined `mentions` variable
                to pass on the Announcement modal for parsing.

                Example result:
                ```
                    mentions = [
                        <@&role_id_here>,
                        ...,
                        ..., # and so on
                    ]
                ```
                """

                for role in roles.values:
                    mentions.append(role.mention)  # Append the mentions.

                await interaction.response.send_message("Role select successful.", ephemeral=True)
                view.stop()  # Stop the view once finished

            view = View(timeout=120)
            roles = RoleSelect(placeholder="Select roles to mention", max_values=25)
            roles.callback = role_callback
            view.add_item(roles)
            await interaction.response.send_message(view=view, ephemeral=True)
            await view.wait()

        elif self.mention == "everyone":
            # Just append the default role mention, `@everyone`
            mentions.append(str(interaction.guild.default_role))

        # The announcement body from the modal
        announcement = f'**{self.announcement_title.value}**\n\n{self.announcement.value}'
        # New if block, mainly for parsing mentions
        if mentions and "$mention" in announcement:
            # This only gets triggered if the list of mentions is not empty and theres a $mention flag
            # inside the announcement body

            # format the number of roles supplied only.
            new_announcement = announcement.replace("$mention", "{}", len(mentions))
            announcement = new_announcement.format(*mentions[:len(mentions)])
        else:
            # Else if no mention queries, just join the list and put it in front.
            announcement = f"{' '.join(mentions)}\n{announcement}"

        await self.channel.send(announcement, file=photo)

        if interaction.response.is_done():  # if the interaction has been responded to before
            await interaction.followup.send("Announcement sent.", ephemeral=True)
        else:
            await interaction.response.send_message("Announcement sent.", ephemeral=True)

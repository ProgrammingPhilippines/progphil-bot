from discord import Interaction, app_commands
from logging import Logger
from discord.ext.commands import check, Context


def is_staff(command_type: str = "app") -> check:
    """A decorator for checking if the
    command invoker is a staff

    Example:
    ```
        # APP_COMMAND
        @is_staff()
        @command(description='Bans a member')
        @describe(member='the member to ban')
        async def ban(interaction: discord.Interaction, member: discord.Member):
            await interaction.response.send_message(f'Banned {member}')

        # PREFIX_COMMAND
        @is_staff(command_type="prefix")
        @prefixed_command(description='Bans a member')
        @describe(member='the member to ban')
        async def ban(interaction: discord.Interaction, member: discord.Member):
            await interaction.response.send_message(f'Banned {member}')
    ```
    """
    async def predicate(interaction: Interaction | Context) -> bool:
        logger: Logger = None
        guild_config = None

        if command_type == "app":
            logger = interaction.client.logger
            guild_config = interaction.client.config.guild
        else:
            logger = interaction.bot.logger
            guild_config = interaction.bot.config.guild

        staff_roles = set(guild_config.staff_roles)

        for id_ in staff_roles:
            role = interaction.guild.get_role(id_)

            if command_type == "app":
                if role in interaction.user.roles:
                    return True
            else:
                if role in interaction.author.roles:
                    return True

        if command_type == "app":
            logger.info(f'{interaction.user} tried to use a staff command')
        else:
            logger.info(f'{interaction.author} tried to use a staff command')

        return False

    if command_type == "app":
        return app_commands.check(predicate)
    elif command_type == "prefix":
        return check(predicate)
    else:
        raise ValueError(f'Invalid command type: {command_type}')

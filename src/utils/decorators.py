from discord import Interaction, app_commands

from src.interface.progphil import IProgPhilBot


def is_staff():
    """A decorator for checking if the
    command invoker is a staff

    Example:
    ```
        @is_staff()
        @command(description='Bans a member')
        @describe(member='the member to ban')
        async def ban(interaction: discord.Interaction, member: discord.Member):
            await interaction.response.send_message(f'Banned {member}')
    ```
    """
    async def predicate(interaction: Interaction[IProgPhilBot]) -> bool:
        guild_config = interaction.client.config.guild()
        staff = False

        for id_ in guild_config.staff_roles:
            role = interaction.guild.get_role(id_)

            if role in interaction.user.roles:
                staff = True
                break  # Break the loop and continue the comand if the invoker is a staff

        return staff

    return app_commands.check(predicate)

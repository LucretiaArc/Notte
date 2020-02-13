import hook
import logging

logger = logging.getLogger(__name__)


async def on_init(discord_client):
    hook.Hook.get("public!command").attach(command)


async def command(message, args):
    """
    This command is a template for other commands. This docstring will appear as the help section for this command.
    """
    pass


hook.Hook.get("on_init").attach(on_init)

from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("public!command").attach(command)


async def command(message, args):
    """
    This command is a template for other commands. This docstring will appear as the help section for this command.
    """
    pass


Hook.get("on_init").attach(on_init)

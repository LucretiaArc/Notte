from hook import Hook

client = None
config = None


async def on_init(discord_client, module_config):
    global client, config
    client = discord_client
    config = module_config

    Hook.get("public!command").attach(command)


async def command(message, args):
    pass


Hook.get("on_init").attach(on_init)

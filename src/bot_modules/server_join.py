import config
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("on_server_join").attach(add_config)


async def add_config(server):
    config.get_server_config(server.id)


Hook.get("on_init").attach(on_init)

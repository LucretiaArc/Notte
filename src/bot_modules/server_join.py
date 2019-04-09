import config
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("on_guild_join").attach(add_config)


async def add_config(guild):
    config.get_guild_config(guild)


Hook.get("on_init").attach(on_init)

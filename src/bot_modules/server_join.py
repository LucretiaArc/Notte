import config
import hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    hook.Hook.get("on_guild_join").attach(add_config)


async def add_config(guild):
    config.get_guild_config(guild)


hook.Hook.get("on_init").attach(on_init)

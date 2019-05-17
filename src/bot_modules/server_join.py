import logging
import config
import discord
import hook

logger = logging.getLogger(__name__)

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    hook.Hook.get("on_guild_join").attach(add_config)


async def add_config(guild: discord.Guild):
    logger.info("Joined guild {0} ({1})".format(guild.id, guild.name))
    config.get_guild_config(guild)


hook.Hook.get("on_init").attach(on_init)

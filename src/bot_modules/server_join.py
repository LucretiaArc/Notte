import logging
import config
import discord
import hook

logger = logging.getLogger(__name__)


async def on_init(discord_client):
    hook.Hook.get("on_guild_join").attach(add_config)


async def add_config(guild: discord.Guild):
    logger.info(f"Joined guild {guild.id} ({guild.name})")
    config.get_guild(guild)


hook.Hook.get("on_init").attach(on_init)

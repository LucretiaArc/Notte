from hook import Hook
import discord
import asyncio
import random

client = None
config = None


async def on_init(discord_client, module_config):
    global client, config
    client = discord_client
    config = module_config
    change_status()


def change_status():
    asyncio.ensure_future(client.change_presence(game=discord.Game(name=random.choices(config["random_statuses"])[0])))
    asyncio.get_event_loop().call_later(600, change_status)


Hook.get("on_init").attach(on_init)

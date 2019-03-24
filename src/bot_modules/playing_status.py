import discord
import asyncio
import random
import config
from hook import Hook

client = None


async def on_init(discord_client):
    global client
    client = discord_client
    change_status()


def change_status():
    asyncio.ensure_future(client.change_presence(game=discord.Game(name=random.choices(config.get_global_config()["random_statuses"])[0])))
    asyncio.get_event_loop().call_later(600, change_status)


Hook.get("on_init").attach(on_init)
